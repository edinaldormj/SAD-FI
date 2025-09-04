from pathlib import Path
from io import StringIO
import pandas as pd
import unicodedata
from presentation.logging_setup import logger

def _norm_cols(df):
    def _nc(c: str) -> str:
        c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode("ascii")
        return c.strip().lower().replace("-", "_").replace(" ", "_")
    df.columns = [_nc(c) for c in df.columns]
    return df

def _fix_text(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    t = s
    if "Ã" in t or "Â" in t:
        try: t = t.encode("latin1").decode("utf-8")
        except Exception: pass
    return unicodedata.normalize("NFC", t).strip()

def _norm_sistema(x: str) -> str | None:
    s = (x or "").upper().replace("_", "-")
    if "IPCA" in s: return "SAC_IPCA"
    if "SAC" in s and "TR" in s: return "SAC_TR"
    if "SAC" in s: return "SAC"
    return None

def _parse_taxa(v) -> float | None:
    if v is None: return None
    if isinstance(v, (int, float)):
        return float(v)/100.0 if float(v) >= 1.5 else float(v)
    s = str(v).strip()
    if not s: return None
    s = s.replace("%", "").replace("a.a.", "").replace("a.a", "").replace("aa", "").replace(",", ".")
    s = "".join(s.split())
    try:
        x = float(s)
        return x/100.0 if x >= 1.5 else x
    except Exception:
        return None

def agregar_bancos_csv(dest: str, fontes_dir: str = "dados/fontes_bancos", taxa_default: float = 0.11):
    src_dir = Path(fontes_dir)
    dest_p = Path(dest); dest_p.parent.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(src_dir.glob("*.csv"))

    if not arquivos:
        minimo = pd.DataFrame([
            {"nome": "Banco A", "sistema": "SAC",      "taxa_anual": taxa_default},
            {"nome": "Banco B", "sistema": "SAC_TR",   "taxa_anual": taxa_default},
            {"nome": "Banco C", "sistema": "SAC_IPCA", "taxa_anual": taxa_default},
        ])
        minimo.to_csv(dest_p, index=False, encoding="utf-8")
        logger.warning("Fallback aplicado (mínimo) → %s", dest_p)
        return str(dest_p), "CSV mínimo criado (fallback)."

    linhas, com_default = [], 0
    for f in arquivos:
        # encoding + separador
        txt = None
        for enc in ("utf-8", "latin1"):
            try:
                txt = f.read_text(encoding=enc)
                break
            except Exception:
                continue
        if txt is None:
            logger.warning("Ignorado (encoding): %s", f); continue
        sep = ";" if txt.count(";") > txt.count(",") else ","
        try:
            df = pd.read_csv(StringIO(txt), sep=sep, engine="python")
        except Exception as e:
            logger.warning("Ignorado (parse: %s): %s", e, f); continue

        df = _norm_cols(df)

        nome = None
        for c in ("banco","instituicao","instituicao_financeira","origem","nome","oferta"):
            if c in df.columns: nome = df[c].astype(str).map(_fix_text); break
        if nome is None: nome = pd.Series([_fix_text(f.stem)] * len(df))

        tipo = None
        for c in ("sistema","tipo","modalidade","produto","linha","modalidade_financiamento"):
            if c in df.columns: tipo = df[c].astype(str); break
        if tipo is None: tipo = pd.Series([f.stem] * len(df))

        taxa_cols = [c for c in df.columns if any(k in c for k in ["taxa_anual","taxa_aa","taxa","juros","nominal","base"])]
        taxa = pd.Series([None]*len(df))
        for c in taxa_cols:
            parsed = df[c].map(_parse_taxa)
            taxa = taxa.where(taxa.notna(), parsed)

        sist = tipo.map(_norm_sistema)

        for n, s, t in zip(nome, sist, taxa):
            if s is None: continue
            if t is None: t = float(taxa_default); com_default += 1
            linhas.append({"nome": _fix_text(str(n).split(" — ")[0].split(" - ")[0]),
                           "sistema": s, "taxa_anual": float(t)})

    if not linhas:
        return agregar_bancos_csv(dest, fontes_dir, taxa_default)

    final = pd.DataFrame(linhas).drop_duplicates(subset=["nome","sistema"])
    final.to_csv(dest_p, index=False, encoding="utf-8")
    logger.info("Agregado %d arquivo(s) → %s (%d linhas; %d com taxa_default=%.4f)",
                len(arquivos), dest_p, len(final), com_default, taxa_default)
    msg = f"Agregado {len(arquivos)} arquivo(s). Linhas: {len(final)}"
    if com_default: msg += f" — {com_default} com taxa_default={taxa_default:.4f}"
    return str(dest_p), msg
