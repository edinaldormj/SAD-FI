# --- bootstrap de imports: garante que 'src' está no sys.path ---
import sys
from pathlib import Path
SRC = Path(__file__).resolve().parents[1]  # .../src
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
# ---------------------------------------------------------------

from application.controlador import ControladorApp
import matplotlib.pyplot as plt
import pandas as pd
from presentation.ui_state import FinanciamentoInput, FontesInput
from presentation.formatters import brl
import streamlit as st
from matplotlib.ticker import FuncFormatter
import re, unicodedata
from io import StringIO

# --- LOG: configuração básica e helper de estatísticas de arquivo ---
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    force=True,  # garante que este formato/nível prevaleça
)
logger = logging.getLogger("sadfi.ui")

def _file_stat(path_str: str) -> str:
    """Resumo legível: tamanho e mtime, ou 'não encontrado'."""
    p = Path(path_str)
    try:
        if not p.exists():
            return f"{path_str} (não encontrado)"
        size_kb = p.stat().st_size / 1024
        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        return f"{path_str} ({size_kb:.1f} KB, mtime {mtime})"
    except Exception as e:
        return f"{path_str} (erro ao inspecionar: {e})"
# -------------------------------------------------------------------


# ---------------- utilitários de arquivo (uploads e agregador/fallback) ----------------
def save_upload(uploaded_file, dest_path: str) -> str:
    """Salva o arquivo enviado no caminho informado (criando diretórios)."""
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = uploaded_file.read()
    dest.write_bytes(data)
    return str(dest)

def atualizar_bancos_csv(
    dest: str = "dados/bancos.csv",
    fontes_dir: str = "dados/fontes_bancos",
    taxa_default: float = 0.11,  # usa a taxa da UI como fallback
):
    """
    Agrega *.csv de `dados/fontes_bancos/` em um único bancos.csv com as colunas
    exigidas pelo leitor: nome, sistema, taxa_anual.

    - Detecta encoding (utf-8; fallback latin1) e separador (',' ou ';').
    - Normaliza modalidade para {SAC, SAC_TR, SAC_IPCA}.
    - Converte taxa anual para fração (ex.: '11,5%' -> 0.115).
    - Fallback: se não houver fontes, cria mínimo com 3 linhas.

    Retorna: (caminho_destino, mensagem_resumo)
    """
    from io import StringIO
    import pandas as pd

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
        # tentativas rápidas de corr. de mojibake comuns
        if "Ã" in t or "Â" in t:
            try: t = t.encode("latin1").decode("utf-8")
            except Exception: pass
        t = unicodedata.normalize("NFC", t)
        return t.strip()

    def _norm_sistema(x: str) -> str | None:
        s = (x or "").upper().replace("_", "-")
        if "IPCA" in s: return "SAC_IPCA"
        if "SAC" in s and "TR" in s: return "SAC_TR"
        if "SAC" in s: return "SAC"
        return None

    def _parse_taxa(v) -> float | None:
        if v is None: return None
        if isinstance(v, (int, float)):
            # já numérico; se >= 1.5 assumimos % e convertemos para fração
            return float(v)/100.0 if float(v) >= 1.5 else float(v)
        s = str(v).strip()
        if not s: return None
        s = s.replace("%", "").replace("a.a.", "").replace("a.a", "").replace("aa", "")
        s = s.replace(",", ".")
        # remove espaços
        s = "".join(s.split())
        try:
            x = float(s)
            return x/100.0 if x >= 1.5 else x
        except Exception:
            return None

    src_dir = Path(fontes_dir)
    dest_p = Path(dest); dest_p.parent.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(src_dir.glob("*.csv"))

    if not arquivos:
        # Fallback mínimo compatível com o leitor
        minimo = pd.DataFrame([
            {"nome": "Banco A", "sistema": "SAC",      "taxa_anual": taxa_default},
            {"nome": "Banco B", "sistema": "SAC_TR",   "taxa_anual": taxa_default},
            {"nome": "Banco C", "sistema": "SAC_IPCA", "taxa_anual": taxa_default},
        ])
        minimo.to_csv(dest_p, index=False, encoding="utf-8")
        logger.warning("Fallback aplicado (mínimo gerado) → %s", dest_p)
        return str(dest_p), "CSV mínimo criado (fallback)."

    linhas = []
    usados, com_default = 0, 0

    for f in arquivos:
        # encoding
        txt = None
        for enc in ("utf-8", "latin1"):
            try:
                txt = f.read_text(encoding=enc)
                break
            except Exception:
                continue
        if txt is None:
            logger.warning("Ignorado (encoding ilegível): %s", f)
            continue

        sep = ";" if txt.count(";") > txt.count(",") else ","
        try:
            df = pd.read_csv(StringIO(txt), sep=sep, engine="python")
        except Exception as e:
            logger.warning("Ignorado (erro de parsing %s): %s", e, f)
            continue

        df = _norm_cols(df)

        # candidatos de nome do banco / instituição
        nome_series = None
        for c in ("banco","instituicao","instituicao_financeira","origem","nome","oferta"):
            if c in df.columns:
                nome_series = df[c].astype(str).map(_fix_text)
                break
        if nome_series is None:
            # usa o nome do arquivo como última alternativa
            nome_series = pd.Series([_fix_text(f.stem)] * len(df))

        # candidatos de modalidade
        tipo_series = None
        for c in ("sistema","tipo","modalidade","produto","linha","modalidade_financiamento"):
            if c in df.columns:
                tipo_series = df[c].astype(str)
                break
        if tipo_series is None:
            tipo_series = pd.Series([f.stem] * len(df))

        # taxa anual: tenta várias colunas comuns
        taxa_cols = [c for c in df.columns if any(k in c for k in
            ["taxa_anual","taxa_aa","taxa","juros","nominal","base"])]
        # constroi série de taxa pegando a primeira coluna que renderizar número
        taxa_series = pd.Series([None]*len(df))
        for c in taxa_cols:
            parsed = df[c].map(_parse_taxa)
            taxa_series = taxa_series.where(taxa_series.notna(), parsed)

        # normaliza sistema e taxa
        sistema_series = tipo_series.map(_norm_sistema)

        for nome, sist, taxa in zip(nome_series, sistema_series, taxa_series):
            if sist is None:
                continue  # sem modalidade reconhecida, ignora
            if taxa is None:
                taxa = float(taxa_default)
                com_default += 1
            linhas.append({
                "nome": _fix_text(nome.split(" — ")[0].split(" - ")[0]),
                "sistema": sist,
                "taxa_anual": float(taxa),
                # colunas auxiliares que não atrapalham o leitor:
                "Oferta": f"{_fix_text(nome.split(' — ')[0].split(' - ')[0])} — " +
                          ({"SAC":"SAC","SAC_TR":"SAC TR","SAC_IPCA":"SAC IPCA+"}[sist]),
                "Tipo": sist,
            })
            usados += 1

    if not linhas:
        logger.warning("Nenhum registro válido agregado; gerando mínimo.")
        return atualizar_bancos_csv(dest=dest, fontes_dir=fontes_dir, taxa_default=taxa_default)

    final = pd.DataFrame(linhas)
    final = final.drop_duplicates(subset=["nome","sistema"], keep="first")
    final.to_csv(dest_p, index=False, encoding="utf-8")

    logger.info(
        "Agregado %d arquivo(s) → %s (%d linhas; %d com taxa_default=%.4f)",
        len(arquivos), dest_p, len(final), com_default, taxa_default
    )
    msg = f"Agregado {len(arquivos)} arquivo(s). Linhas: {len(final)}"
    if com_default:
        msg += f" — {com_default} linha(s) usaram taxa_default={taxa_default:.4f}"
    return str(dest_p), msg
# ---------------------------------------------------------------------------

st.set_page_config(page_title="SAD-FI — Comparador", layout="wide")
st.title("SAD-FI — Comparador de Financiamentos (SAC, SAC-TR, SAC+IPCA)")

# Inputs
col1, col2 = st.columns(2)
with col1:
    fin = FinanciamentoInput(
        valor_total=st.number_input("Valor do imóvel", 0.0, 10_000_000.0, 300_000.0, step=1_000.0),
        entrada=st.number_input("Entrada", 0.0, 9_999_999.0, 60_000.0, step=1_000.0),
        prazo_anos=st.number_input("Prazo (anos)", 1, 40, 30, step=1),
        taxa_juros_anual=st.number_input("Taxa base a.a. (fração)", 0.0, 1.0, 0.11, step=0.005),
    )

with col2:
    fontes = FontesInput(
        caminho_bancos=st.text_input("Caminho bancos.csv", "dados/bancos.csv"),
        caminho_ipca=st.text_input("Caminho IPCA (CSV Bacen)", "dados/txjuros/IPCA_BACEN.csv"),
        caminho_tr_compat=st.text_input("Caminho TR (mensal compat.)", "dados/txjuros/TR_mensal_compat.csv"),
    )

    # Uploads opcionais — salvam no caminho definido acima
    up_bancos = st.file_uploader("Enviar bancos.csv (opcional)", type=["csv"], key="up_bancos")
    if up_bancos is not None:
        fontes.caminho_bancos = save_upload(up_bancos, fontes.caminho_bancos)
        st.success(f"bancos.csv salvo em: {fontes.caminho_bancos}")

    up_ipca = st.file_uploader("Enviar IPCA_BACEN.csv (opcional)", type=["csv"], key="up_ipca")
    if up_ipca is not None:
        fontes.caminho_ipca = save_upload(up_ipca, fontes.caminho_ipca)
        st.success(f"IPCA salvo em: {fontes.caminho_ipca}")

    up_tr = st.file_uploader("Enviar TR_mensal_compat.csv (opcional)", type=["csv"], key="up_tr")
    if up_tr is not None:
        fontes.caminho_tr_compat = save_upload(up_tr, fontes.caminho_tr_compat)
        st.success(f"TR salva em: {fontes.caminho_tr_compat}")

    # Botão para gerar/atualizar bancos.csv agregando fontes locais (fallback se vazio)
    if st.button("Atualizar bancos.csv (agregar fontes locais)"):
        caminho, msgupd = atualizar_bancos_csv(
            dest=fontes.caminho_bancos,
            taxa_default=fin.taxa_juros_anual,  # << usa a taxa da UI como fallback
        )
        fontes.caminho_bancos = caminho
        st.info(msgupd)
        st.success(f"bancos.csv atualizado em: {caminho}")


st.caption(f"Usando bancos: {fontes.caminho_bancos} | IPCA: {fontes.caminho_ipca} | TR: {fontes.caminho_tr_compat}")

# LOG: fontes com tamanho/mtime para auditoria rápida no terminal
logger.info(
    "Fontes selecionadas | bancos=%s | IPCA=%s | TR=%s",
    _file_stat(fontes.caminho_bancos),
    _file_stat(fontes.caminho_ipca),
    _file_stat(fontes.caminho_tr_compat),
)


# === HOTFIX DE SCHEMA PARA bancos.csv ===
import io, csv, re

def _detect_sep_for_csv(path: str) -> str:
    try:
        txt = Path(path).read_text(encoding="utf-8")
    except Exception:
        txt = Path(path).read_text(encoding="latin1")
    return ";" if txt.count(";") > txt.count(",") else ","

_missing_cols_re = re.compile(r"faltam colunas obrigat[oó]rias:\s*\[(.*?)\]", re.IGNORECASE)

def _parse_missing_from_error(err_msg: str) -> list[str]:
    m = _missing_cols_re.search(err_msg or "")
    if not m:
        return []
    inner = m.group(1)
    # extrai 'nome', 'sistema', 'taxa_anual' etc.
    cols = re.findall(r"'([^']+)'|\"([^\"]+)\"", inner)
    cols = [a or b for (a, b) in cols]
    # fallback bruto
    if not cols:
        cols = [c.strip().strip("'\"") for c in inner.split(",")]
    return [c for c in (c.strip() for c in cols) if c]

def _norm_modalidade_str(s: str | None) -> str | None:
    s = (s or "").upper().replace("_", "-")
    if "IPCA" in s: return "SAC_IPCA"
    if "SAC" in s and "TR" in s: return "SAC_TR"
    if "SAC" in s: return "SAC"
    return None

def _parse_taxa_to_frac(v) -> float | None:
    if v is None: return None
    if isinstance(v, (int, float)):
        return float(v)/100.0 if float(v) >= 1.5 else float(v)
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

def _ensure_bancos_schema(bancos_path: str, required_cols: list[str], taxa_default: float) -> None:
    """Garante que bancos.csv tenha as colunas exigidas pelo leitor (criando/renomeando se preciso)."""
    sep = _detect_sep_for_csv(bancos_path)
    # tenta utf-8; fallback latin1
    import pandas as pd, unicodedata as _ud
    def _read(p, enc):
        return pd.read_csv(p, sep=sep, engine="python", encoding=enc)
    try:
        df = _read(bancos_path, "utf-8")
    except Exception:
        df = _read(bancos_path, "latin1")

    # normaliza cabeçalhos
    def _nc(c: str) -> str:
        c = _ud.normalize("NFKD", str(c)).encode("ascii","ignore").decode("ascii")
        return c.strip().lower().replace("-", "_").replace(" ", "_")
    df.columns = [_nc(c) for c in df.columns]

    # mapear sinônimos -> campos-alvo
    # alvo provável do leitor: 'nome', 'sistema', 'taxa_anual'
    # (se o leitor pedir nomes diferentes, usamos a lista `required_cols`)
    synonyms = {
        "nome": ["nome","banco","instituicao","instituicao_financeira","origem","oferta"],
        "sistema": ["sistema","tipo","modalidade","produto","linha","modalidade_financiamento","Tipo"],
        "taxa_anual": ["taxa_anual","taxa_aa","taxa","juros","nominal","base","taxa_juros_anual"],
    }

    # cria colunas ausentes a partir de sinônimos
    if "nome" not in df.columns:
        for cand in synonyms["nome"]:
            if cand in df.columns:
                df["nome"] = df[cand]
                break
        if "nome" not in df.columns:
            # tenta derivar de 'Oferta' se existir na forma original (case-insensitive)
            # ou usa nome genérico
            if "oferta" in df.columns and df["oferta"].notna().any():
                df["nome"] = df["oferta"].astype(str).str.split(r"\s+[—-]\s+", regex=True).str[0]
            else:
                df["nome"] = "Banco"

    if "sistema" not in df.columns:
        for cand in synonyms["sistema"]:
            if cand in df.columns:
                df["sistema"] = df[cand]
                break
        if "sistema" not in df.columns:
            df["sistema"] = ""

    df["sistema"] = df["sistema"].map(_norm_modalidade_str)

    if "taxa_anual" not in df.columns:
        for cand in synonyms["taxa_anual"]:
            if cand in df.columns:
                df["taxa_anual"] = df[cand].map(_parse_taxa_to_frac)
                break
        if "taxa_anual" not in df.columns:
            df["taxa_anual"] = None

    # completa faltantes com defaults
    df["nome"] = df["nome"].fillna("Banco").astype(str)
    df["sistema"] = df["sistema"].fillna("")
    df["taxa_anual"] = df["taxa_anual"].map(lambda x: taxa_default if (x is None or (isinstance(x,float) and x!=x)) else x)

    # filtra linhas válidas (precisa de sistema reconhecido)
    df_ok = df[df["sistema"].isin(["SAC","SAC_TR","SAC_IPCA"])].copy()
    if df_ok.empty:
        # se vazio, cria mínimo válido
        df_ok = pd.DataFrame([
            {"nome":"Banco A","sistema":"SAC","taxa_anual":taxa_default},
            {"nome":"Banco B","sistema":"SAC_TR","taxa_anual":taxa_default},
            {"nome":"Banco C","sistema":"SAC_IPCA","taxa_anual":taxa_default},
        ])

    # se o leitor pediu nomes diferentes de 'nome/sistema/taxa_anual', alinhe-os
    rename_map = {}
    target_set = set(required_cols) if required_cols else {"nome","sistema","taxa_anual"}
    std_to_target = {
        "nome": next((c for c in required_cols if c.lower() in {"nome","banco"}), "nome") if required_cols else "nome",
        "sistema": next((c for c in required_cols if c.lower() in {"sistema","tipo"}), "sistema") if required_cols else "sistema",
        "taxa_anual": next((c for c in required_cols if "taxa" in c.lower()), "taxa_anual") if required_cols else "taxa_anual",
    }
    for k,std in [("nome","nome"),("sistema","sistema"),("taxa_anual","taxa_anual")]:
        tgt = std_to_target[std]
        if std != tgt:
            rename_map[std] = tgt

    df_ok = df_ok.rename(columns=rename_map)

    # mantém apenas colunas necessárias + extras não conflituosas
    needed = list(target_set) if required_cols else ["nome","sistema","taxa_anual"]
    extras = [c for c in df_ok.columns if c not in needed]
    df_ok = df_ok[needed + extras]

    # salva de volta como UTF-8 com vírgula
    df_ok.to_csv(bancos_path, index=False, encoding="utf-8")
    logger.warning("bancos.csv foi ajustado para conter colunas obrigatórias: %s", needed)
# === FIM HOTFIX ===



run = st.button("Executar comparação")

if run:
    # Contrato do controlador preservado
    fonte_ipca = {"caminho_ipca": fontes.caminho_ipca}
    fonte_tr   = {"fixture_csv_path": fontes.caminho_tr_compat}

    logger.info(
        "Executando simulação | valor_total=%.2f, entrada=%.2f, prazo_anos=%d, taxa_juros_anual=%.4f",
        fin.valor_total, fin.entrada, fin.prazo_anos, fin.taxa_juros_anual
    )

    try:
        resultados, ranking, msg = ControladorApp().simular_multiplos_bancos(
            caminho_bancos_csv=fontes.caminho_bancos,
            dados_financiamento={
                "valor_total": fin.valor_total,
                "entrada": fin.entrada,
                "prazo_anos": fin.prazo_anos,
                "taxa_juros_anual": fin.taxa_juros_anual,
            },
            fonte_ipca={"caminho_ipca": fontes.caminho_ipca},
            fonte_tr={"fixture_csv_path": fontes.caminho_tr_compat},
        )
    except ValueError as e:
        err = str(e)
        missing = _parse_missing_from_error(err)
        logger.error("Falha ao carregar bancos.csv: %s", err)
        if missing:
            # tenta corrigir e rodar de novo
            _ensure_bancos_schema(fontes.caminho_bancos, missing, fin.taxa_juros_anual)
            logger.info("Tentando novamente após corrigir colunas ausentes: %s", missing)
            resultados, ranking, msg = ControladorApp().simular_multiplos_bancos(
                caminho_bancos_csv=fontes.caminho_bancos,
                dados_financiamento={
                    "valor_total": fin.valor_total,
                    "entrada": fin.entrada,
                    "prazo_anos": fin.prazo_anos,
                    "taxa_juros_anual": fin.taxa_juros_anual,
                },
                fonte_ipca={"caminho_ipca": fontes.caminho_ipca},
                fonte_tr={"fixture_csv_path": fontes.caminho_tr_compat},
            )
        else:
            # sem dica das colunas, exibe erro amigável e aborta
            st.error(f"Erro ao ler bancos.csv: {err}")
            raise


    st.subheader("Ranking")
    df_rank = pd.DataFrame(ranking, columns=["Oferta", "Total Pago"])
    st.dataframe(df_rank.style.format({"Total Pago": brl}), use_container_width=True)

    # LOG: resumo do ranking
    if not df_rank.empty:
        i_min = int(df_rank["Total Pago"].idxmin())
        i_max = int(df_rank["Total Pago"].idxmax())
        logger.info(
            "Ranking gerado | ofertas=%d | menor=%.2f (%s) | maior=%.2f (%s)",
            len(df_rank),
            float(df_rank.loc[i_min, "Total Pago"]), df_rank.loc[i_min, "Oferta"],
            float(df_rank.loc[i_max, "Total Pago"]), df_rank.loc[i_max, "Oferta"],
        )
    else:
        logger.warning("Ranking vazio após simulação.")

    logger.info("Mensagem da simulação: %s", msg.strip() if isinstance(msg, str) else msg)

    # Export CSV de ranking
    out_dir = Path("resultados"); out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ranking.csv").parent.mkdir(parents=True, exist_ok=True)
    df_rank.to_csv(out_dir / "ranking.csv", index=False, encoding="utf-8")
    st.caption(f"CSV salvo em: {out_dir/'ranking.csv'}")
    logger.info("Arquivo salvo: %s", (out_dir / "ranking.csv").resolve())

    st.info(msg)

    # --- Ranking: barras horizontais com correção de encoding e margem dinâmica ---
    def _fmt_brl_axis(x, pos):
        return "R$ " + f"{x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    _C1_RE = re.compile(r"[\u0080-\u009F]")  # controles C1 (inclui U+0081, U+009A etc.)

    def fix_text(s: str) -> str:
        """Corrige mojibake comum e remove controles C1."""
        if not isinstance(s, str):
            s = str(s)
        t = s

        # Caso típico UTF-8 lido como Latin-1: "SÃ£o" -> "São"
        if "Ã" in t or "Â" in t:
            try:
                t = t.encode("latin1").decode("utf-8")
            except Exception:
                pass

        # Se houver controles C1, reinterpretar como CP1252; se falhar, remover
        if _C1_RE.search(t):
            try:
                t = t.encode("latin1").decode("cp1252")
            except Exception:
                t = _C1_RE.sub("", t)

        t = unicodedata.normalize("NFC", t)
        return t.strip()

    st.subheader("Ranking — Total Pago")

    # Ordena do mais barato ao mais caro e corrige rótulos
    df_plot = df_rank.copy()
    df_plot["Oferta"] = df_plot["Oferta"].astype(str).map(fix_text)
    df_plot = df_plot.sort_values("Total Pago", ascending=True).reset_index(drop=True)
    n = len(df_plot)

    # Cores: gradiente verde→vermelho
    cmap = plt.get_cmap("RdYlGn_r")
    colors = [cmap(i / (n - 1) if n > 1 else 0.0) for i in range(n)]

    fig_r, ax_r = plt.subplots(figsize=(11, 0.6 * n + 1.2))
    bars = ax_r.barh(df_plot["Oferta"], df_plot["Total Pago"], color=colors, edgecolor="none")

    # Eixo X como moeda
    xmax = float(df_plot["Total Pago"].max()) if n else 1.0
    ax_r.xaxis.set_major_formatter(FuncFormatter(_fmt_brl_axis))

    # Margem inicial + ajuste de rótulos
    ax_r.set_xlim(0, xmax * 1.10)
    ax_r.margins(x=0.02)

    need_external = False
    max_label_chars = 0

    for bar, valor in zip(bars, df_plot["Total Pago"]):
        label = brl(valor)
        max_label_chars = max(max_label_chars, len(label))
        frac = (valor / xmax) if xmax else 0.0
        if frac >= 0.18:
            # dentro da barra (texto branco, alinhado à direita)
            x = bar.get_width() - 0.01 * xmax
            ax_r.text(x, bar.get_y() + bar.get_height() / 2, label,
                      va="center", ha="right", fontsize=10, color="white")
        else:
            # fora da barra (pequena folga)
            x = bar.get_width() + 0.01 * xmax
            ax_r.text(x, bar.get_y() + bar.get_height() / 2, label,
                      va="center", ha="left", fontsize=10)
            need_external = True

    # Se houve rótulos externos, amplia o limite do eixo X proporcional ao tamanho dos rótulos
    if need_external:
        extra = 0.03 + 0.012 * max_label_chars  # margem ~3% + 1.2% por caractere
        ax_r.set_xlim(0, xmax * (1.0 + min(extra, 0.40)))  # teto de +40%

    ax_r.invert_yaxis()  # mais barato no topo
    ax_r.grid(axis="x", alpha=0.25)
    ax_r.set_xlabel("Total Pago")
    ax_r.set_ylabel("Oferta")

    # Salvar PNG do ranking **antes** de exibir e não limpar a figura
    fig_r.tight_layout()
    fig_r.canvas.draw()
    out_g = out_dir / "graficos"; out_g.mkdir(parents=True, exist_ok=True)
    fig_r.savefig(out_g / "ranking.png", dpi=160, bbox_inches="tight", facecolor="white")
    st.caption(f"PNG salvo em: {out_g/'ranking.png'}")
    logger.info("Arquivo salvo: %s", (out_g / "ranking.png").resolve())
    st.pyplot(fig_r, clear_figure=False)
    # --- fim do ranking ---

    # Gráfico Top-3 (eixo anual)
    def _serie_parcelas(res):
        if hasattr(res, "to_dataframe"):
            try:
                df = res.to_dataframe()
                if {"n_parcela", "valor_parcela"}.issubset(df.columns):
                    return df["n_parcela"].tolist(), df["valor_parcela"].tolist()
            except Exception:
                pass
        px = [getattr(p, "numero", i + 1) for i, p in enumerate(res.parcelas)]
        py = [float(p.valor_total) for p in res.parcelas]
        return px, py

    def _fmt_brl(x, pos):
        # R$ 1.234 (sem casas) para não poluir o eixo
        return "R$ " + f"{x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    st.subheader("Evolução do valor da parcela — Top 3")
    top3 = ranking[:3]

    fig, ax = plt.subplots(figsize=(11, 5))
    for rotulo, _ in top3:
        x, y = _serie_parcelas(resultados[rotulo])
        ax.plot(x, y, linewidth=2, label=rotulo)

    # Eixo X: rótulos anuais ("Ano N") com redução dinâmica de densidade
    if top3:
        n = max(len(_serie_parcelas(resultados[r])[0]) for r, _ in top3)
        anos = list(range(12, n + 1, 12))  # marcas a cada 12 parcelas
        step = 1
        if len(anos) > 24:  # prazos longos: evita poluição visual
            step = 2
        if len(anos) > 36:
            step = 5
        ax.set_xticks(anos[::step])
        ax.set_xticklabels([f"Ano {i}" for i in range(1, len(anos) + 1)][::step])

    # Eixo Y: moeda legível
    ax.yaxis.set_major_formatter(FuncFormatter(_fmt_brl))

    ax.set_xlabel("Tempo")
    ax.set_ylabel("Valor da parcela")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right", frameon=False)
    ax.margins(x=0)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)
    # --- fim do trecho do Top-3 ---
