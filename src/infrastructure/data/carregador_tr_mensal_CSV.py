from pathlib import Path
from typing import Optional, Union
import pandas as pd

def carregar_tr_mensal(
    path_csv: Union[str, Path],
    data_col: Optional[str] = None,
    valor_col: Optional[str] = None,
    dayfirst: bool = True,
    fill_missing: bool = False,
    start: Optional[str] = None,  # "YYYY-MM"
    end:   Optional[str] = None,  # "YYYY-MM"
) -> pd.DataFrame:
    """
    Lê TR diária exportada do Bacen e retorna uma tabela mensal (colunas: data [YYYY-MM], tr [float]).
    Estratégia:
      - lê com encoding latin1 e separador ';' (formato padrão dos CSVs do Bacen);
      - detecta automaticamente colunas de data e valor se não informadas;
      - converte data para datetime (dayfirst=True), normaliza valores (','->'.', remove '%');
      - converte para FRAÇÃO se os valores vierem em porcentagem;
      - agrupa por mês e usa o ÚLTIMO valor disponível no mês (prática adequada para TR mensal);
      - opcionalmente reindexa para intervalo start..end e preenche (ffill) se fill_missing=True.

    Retorna DataFrame com colunas ['data','tr'] (data no formato "YYYY-MM").
    """
    path = Path(path_csv)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    # 1) leitura robusta
    df = pd.read_csv(path, encoding="latin1", sep=";")

    # 2) detectar colunas
    cols = list(df.columns)
    if data_col is None:
        data_col = next((c for c in cols if "data" in c.lower()), cols[0])
    if valor_col is None:
        valor_col = next(
            (c for c in cols if any(k in c.lower() for k in ("valor", "tr", "taxa", "indice", "índice"))),
            None,
        )
        if valor_col is None:
            # fallback: pega a segunda coluna se existir
            valor_col = cols[1] if len(cols) > 1 else cols[0]

    # 3) normalização básica
    df = df[[data_col, valor_col]].rename(columns={data_col: "data_raw", valor_col: "tr_raw"}).copy()
    # a data costuma vir em "DD/MM/YYYY" ou "MM/YYYY" — tentamos parse com dayfirst
    df["data_dt"] = pd.to_datetime(df["data_raw"].astype(str).str.strip(), dayfirst=dayfirst, errors="coerce")
    df = df.dropna(subset=["data_dt"]).reset_index(drop=True)

    # normaliza valores: "0,017" -> 0.017 ; "0,17%" -> 0.0017 (mais abaixo convertemos %->frac)
    df["tr_clean"] = (
        df["tr_raw"]
        .astype(str)
        .str.replace(".", "", regex=False)   # remove pontos de milhar (por precaução)
        .str.replace(",", ".", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip()
    )
    df["tr"] = pd.to_numeric(df["tr_clean"], errors="coerce")
    df = df.dropna(subset=["tr"]).reset_index(drop=True)

    # 4) Se estiver em porcentagem (mediana > 1), converte para fração
    med = df["tr"].abs().median()
    if pd.notna(med) and med > 0.02:
        df["tr"] = df["tr"] / 100.0

    # 5) agrega por mês: usar o ÚLTIMO valor do mês (DataTime -> Period M)
    df["ano_mes"] = df["data_dt"].dt.to_period("M").astype(str)  # "YYYY-MM"
    # ordenar por data e pegar último do mês
    df = df.sort_values(["ano_mes", "data_dt"])
    mensal = df.groupby("ano_mes", as_index=False).agg({"tr": "last"}).rename(columns={"ano_mes": "data"})

    # 6) opcional: reindexar para um intervalo contínuo start..end e preencher
    if start is not None or end is not None:
        # determina start/end automáticos se não fornecidos
        min_m = mensal["data"].min() if not mensal.empty else None
        max_m = mensal["data"].max() if not mensal.empty else None
        start = start or min_m
        end   = end   or max_m
        if start is None or end is None:
            # nada para reindexar
            pass
        else:
            rng = pd.period_range(start=start, end=end, freq="M").astype(str)
            df_idx = mensal.set_index("data").reindex(rng)
            if fill_missing:
                df_idx["tr"] = df_idx["tr"].ffill()
            mensal = df_idx.reset_index().rename(columns={"index": "data"})

    # final: garantir ordenação ascendente por data
    mensal = mensal.sort_values("data").reset_index(drop=True)

    return mensal[["data", "tr"]]
