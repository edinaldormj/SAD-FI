from pathlib import Path
from typing import Optional
import re
import pandas as pd

def carregar_ipca_bacen_csv(path_csv: Optional[str | Path]) -> pd.DataFrame:
    """
    Lê um CSV exportado do Bacen para IPCA e retorna DataFrame com colunas:
      - data (YYYY-MM)
      - ipca (float, em FRAÇÃO, ex.: 0.0186 para 1.86%)

    Heurísticas suportadas:
      - detecta colunas cujo nome contenha 'data', 'mes', 'mês', 'periodo' etc.
      - detecta colunas cujo nome contenha 'valor', 'índice', 'indice', 'var', '%' etc.
      - se não houver cabeçalhos óbvios, detecta coluna com padrão 'MM/YYYY' e usa a coluna adjacente como valor
      - aceita arquivos com encoding latin1 e separador ';' (padrão do site do Bacen)
    """
    path = Path(path_csv)
    if not path.exists():
        raise FileNotFoundError(f"IPCA CSV não encontrado: {path}")

    # 1) leitura robusta
    try:
        df_raw = pd.read_csv(path, encoding="latin1", sep=";")
    except Exception:
        # tentativa alternativa mais permissiva
        df_raw = pd.read_csv(path, encoding="latin1", sep=",", engine="python")

    df = df_raw.copy()
    cols = [c.strip() for c in df.columns]

    # 2) localizar coluna de data
    date_col = next((c for c in cols if re.search(r"data|mes|m[eê]s|periodo|per[íi]odo", c, re.I)), None)

    # 3) localizar coluna de valor (ipca)
    value_col = next((c for c in cols if re.search(r"valor|índice|indice|var|var\.|%|ipca", c, re.I)), None)

    # 4) heurística: se não encontrou date_col, tenta achar coluna com formato MM/YYYY
    if date_col is None:
        for c in cols:
            sample = df[c].astype(str).head(50).str.strip()
            if sample.str.match(r"^\d{2}/\d{4}$").any() or sample.str.match(r"^\d{1,2}/\d{1,2}/\d{4}$").any():
                date_col = c
                break

    # 5) heurística: se não encontrou value_col, tenta achar coluna numérica
    if value_col is None:
        for c in cols:
            if c == date_col:
                continue
            sample = df[c].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
            numeric_ratio = pd.to_numeric(sample, errors="coerce").notna().mean()
            if numeric_ratio > 0.6:
                value_col = c
                break

    # 6) caso especial: arquivo com uma única coluna (header = descrição, valores só)
    if value_col is None and len(cols) == 1:
        value_col = cols[0]
        date_col = None  # não há data, precisaremos abortar (ver abaixo)

    # Se ainda não identificou coluna de valor ou data, erro informativo
    if value_col is None or date_col is None:
        sample_display = df.head(8)
        raise ValueError(
            "Não foi possível identificar automaticamente colunas 'data' e/ou 'valor' no CSV do IPCA.\n"
            f"Colunas detectadas: {cols}\n\nAmostra do arquivo:\n{sample_display}\n\n"
            "Se o CSV tiver esquema não padrão, informe explicitamente quais colunas usar "
            "(e.g. passar um DataFrame já tratado) ou renomeie o cabeçalho para 'data' e 'valor'."
        )

    # 7) extrair e normalizar
    out = df[[date_col, value_col]].rename(columns={date_col: "data", value_col: "ipca"}).copy()

    # 7a) normaliza data: aceita "MM/YYYY", "DD/MM/YYYY", "YYYY-MM"
    out["data"] = out["data"].astype(str).str.strip()
    def _to_yyyy_mm(s: str) -> Optional[str]:
        s = (s or "").strip()
        if re.match(r"^\d{2}/\d{4}$", s):   # MM/YYYY
            mm, yyyy = s.split("/")
            return f"{int(yyyy):04d}-{int(mm):02d}"
        if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", s):  # DD/MM/YYYY
            parts = s.split("/")
            d, m, y = parts
            return f"{int(y):04d}-{int(m):02d}"
        if re.match(r"^\d{4}-\d{2}$", s):  # YYYY-MM
            return s[:7]
        if re.match(r"^\d{4}/\d{2}$", s):  # YYYY/MM
            yyyy, mm = s.split("/")
            return f"{int(yyyy):04d}-{int(mm):02d}"
        # fallback: try parse with pandas
        try:
            dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
            if pd.isna(dt):
                return None
            return f"{dt.year:04d}-{dt.month:02d}"
        except Exception:
            return None

    out["data"] = out["data"].map(_to_yyyy_mm)
    out = out.dropna(subset=["data"])

    # 7b) normaliza ipca numérico (',' -> '.', remove '%' e pontos de milhar)
    out["ipca"] = (
        out["ipca"].astype(str)
                  .str.replace(".", "", regex=False)
                  .str.replace(",", ".", regex=False)
                  .str.replace("%", "", regex=False)
                  .str.strip()
    )
    out["ipca"] = pd.to_numeric(out["ipca"], errors="coerce")
    out = out.dropna(subset=["ipca"]).reset_index(drop=True)

    # 8) Se IPCA veio em porcentagem (ex.: 1.86), converte p/ fração (0.0186)
    med = out["ipca"].abs().median()
    if pd.notna(med) and med > 1.0:
        out["ipca"] = out["ipca"] / 100.0

    # 9) ordena por data (YYYY-MM) e remove duplicatas mantendo o primeiro
    out = out.drop_duplicates(subset=["data"], keep="first")
    out = out.sort_values("data").reset_index(drop=True)

    return out[["data", "ipca"]]
