import re
import pandas as pd
import unicodedata
from pathlib import Path
from presentation.logging_setup import logger

_missing_cols_re = re.compile(r"faltam colunas obrigat[oó]rias:\s*\[(.*?)\]", re.IGNORECASE)

def parse_missing_from_error(err_msg: str) -> list[str]:
    m = _missing_cols_re.search(err_msg or "")
    if not m:
        return []
    inner = m.group(1)
    cols = re.findall(r"'([^']+)'|\"([^\"]+)\"", inner)
    cols = [a or b for (a, b) in cols]
    if not cols:
        cols = [c.strip().strip("'\"") for c in inner.split(",")]
    return [c for c in (c.strip() for c in cols) if c]

def _nc(c: str) -> str:
    c = unicodedata.normalize("NFKD", str(c)).encode("ascii","ignore").decode("ascii")
    return c.strip().lower().replace("-", "_").replace(" ", "_")

def _norm_modalidade(s: str | None) -> str | None:
    s = (s or "").upper().replace("_", "-")
    if "IPCA" in s: return "SAC_IPCA"
    if "SAC" in s and "TR" in s: return "SAC_TR"
    if "SAC" in s: return "SAC"
    return None

def _parse_taxa(v) -> float | None:
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)/100.0 if float(v) >= 1.5 else float(v)
    s = str(v).strip()
    if not s: return None
    s = (s.replace("%","").replace("a.a.","").replace("a.a","")
           .replace("aa","").replace(",", "."))
    s = "".join(s.split())
    try:
        x = float(s)
        return x/100.0 if x >= 1.5 else x
    except Exception:
        return None

def ensure_bancos_schema(bancos_path: str, required_cols: list[str], taxa_default: float) -> None:
    p = Path(bancos_path)
    # tenta detectar separador rápido
    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        txt = p.read_text(encoding="latin1")
    sep = ";" if txt.count(";") > txt.count(",") else ","

    try:
        df = pd.read_csv(p, sep=sep, engine="python", encoding="utf-8")
    except Exception:
        df = pd.read_csv(p, sep=sep, engine="python", encoding="latin1")

    df.columns = [_nc(c) for c in df.columns]

    # construir colunas-alvo padrão
    if "nome" not in df.columns:
        for cand in ("banco","instituicao","instituicao_financeira","origem","oferta"):
            if cand in df.columns:
                df["nome"] = df[cand]; break
        if "nome" not in df.columns:
            df["nome"] = "Banco"

    if "sistema" not in df.columns:
        for cand in ("sistema","tipo","modalidade","produto","linha","modalidade_financiamento"):
            if cand in df.columns:
                df["sistema"] = df[cand]; break
        if "sistema" not in df.columns:
            df["sistema"] = ""

    if "taxa_anual" not in df.columns:
        for cand in ("taxa_anual","taxa_aa","taxa","juros","nominal","base","taxa_juros_anual"):
            if cand in df.columns:
                df["taxa_anual"] = df[cand].map(_parse_taxa); break
        if "taxa_anual" not in df.columns:
            df["taxa_anual"] = None

    df["sistema"] = df["sistema"].map(_norm_modalidade)
    df["nome"] = df["nome"].fillna("Banco").astype(str)
    df["taxa_anual"] = df["taxa_anual"].map(lambda x: taxa_default if (x is None or (isinstance(x,float) and x!=x)) else x)

    df_ok = df[df["sistema"].isin(["SAC","SAC_TR","SAC_IPCA"])].copy()
    if df_ok.empty:
        df_ok = pd.DataFrame([
            {"nome":"Banco A","sistema":"SAC","taxa_anual":taxa_default},
            {"nome":"Banco B","sistema":"SAC_TR","taxa_anual":taxa_default},
            {"nome":"Banco C","sistema":"SAC_IPCA","taxa_anual":taxa_default},
        ])

    # alinhar nomes à lista requerida, se vierem diferentes
    rename_map = {}
    if required_cols:
        tgt_nome = next((c for c in required_cols if c.lower() in {"nome","banco"}), "nome")
        tgt_sis  = next((c for c in required_cols if c.lower() in {"sistema","tipo"}), "sistema")
        tgt_tx   = next((c for c in required_cols if "taxa" in c.lower()), "taxa_anual")
        for std, tgt in [("nome",tgt_nome), ("sistema",tgt_sis), ("taxa_anual",tgt_tx)]:
            if std != tgt: rename_map[std] = tgt

    df_ok = df_ok.rename(columns=rename_map)
    need = required_cols if required_cols else ["nome","sistema","taxa_anual"]
    df_ok[need].to_csv(p, index=False, encoding="utf-8")
    logger.warning("bancos.csv ajustado para colunas obrigatórias: %s", need)
