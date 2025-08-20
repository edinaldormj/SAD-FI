"""
Coletor de dados do IPCA (SGS/BACEN), série 433.
- Tenta `bcdata`; fallback via `requests`.
- Retorna DataFrame com colunas: `data` (YYYY-MM) e `ipca` (percentual mensal, ex.: 0.45 para 0,45%).
Observação: a convenção do projeto é armazenar `%` e converter para fração apenas no consumo (TabelaIPCA.get_ipca).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional
import pandas as pd

SGS_IPCA_SERIE = 433
MESES_HISTORICO = 24

def _periodo_padrao(meses: int = MESES_HISTORICO) -> tuple[str, str]:
    fim = date.today().replace(day=1) - timedelta(days=1)  # último dia do mês anterior
    inicio = (fim.replace(day=1) - timedelta(days=(meses-1)*30)).replace(day=1)
    di = f"{inicio.day:02d}/{inicio.month:02d}/{inicio.year}"
    df = f"{fim.day:02d}/{fim.month:02d}/{fim.year}"
    return di, df

def obter_ipca_df(meses: int = MESES_HISTORICO,
                  data_inicial: Optional[str] = None,
                  data_final: Optional[str] = None) -> pd.DataFrame:
    di, df = (data_inicial, data_final)
    if di is None or df is None:
        di, df = _periodo_padrao(meses)
    # 1) Tenta bcdata
    try:
        from bcdata import sgs as _sgs  # type: ignore
        raw = _sgs.get({str(SGS_IPCA_SERIE): SGS_IPCA_SERIE}, start=di, end=df)
        if isinstance(raw, pd.DataFrame):
            # tentar mapear colunas usuais
            col_data = next((c for c in raw.columns if c.lower().startswith(("date","data"))), None)
            col_val = next((c for c in raw.columns if c.lower() in ("ipca","value","valor")), None)
            if col_data is None or col_val is None:
                raise RuntimeError("Formato inesperado do DataFrame em bcdata.sgs.get")
            df_ipca = raw[[col_data, col_val]].rename(columns={col_data:"data", col_val:"ipca"})
            return _normalizar_df(df_ipca)
    except Exception:
        pass
    # 2) Fallback requests
    return _obter_ipca_via_requests(SGS_IPCA_SERIE, di, df)

def _obter_ipca_via_requests(serie: int, data_inicial: str, data_final: str) -> pd.DataFrame:
    import requests
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
    params = {"formato": "json", "dataInicial": data_inicial, "dataFinal": data_final}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    dados = r.json()  # [{'data':'MM/YYYY','valor':'0,45'}, ...]
    df = pd.DataFrame(dados).rename(columns={"valor":"ipca"})
    return _normalizar_df(df)

def _normalizar_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    def norm_data(x: str) -> str:
        x = str(x).strip()
        if "/" in x and len(x) == 7:  # 'MM/YYYY'
            m, y = x.split("/")
            return f"{y}-{int(m):02d}"
        if "-" in x:
            return x[:7]
        return x
    def to_float(v) -> float:
        return float(str(v).replace(",", ".").strip())
    out["data"] = out["data"].map(norm_data)
    out["ipca"] = out["ipca"].map(to_float)
    out = out.dropna(subset=["ipca"]).sort_values("data").reset_index(drop=True)
    return out[["data","ipca"]]

def df_para_tabela_ipca(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adapta o DataFrame para o formato consumido por TabelaIPCA (armazenamento em %).
    Não converter para fração aqui.
    """
    out = df.copy()
    assert {"data","ipca"}.issubset(out.columns)
    return out
