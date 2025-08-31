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

def atualizar_bancos_csv(dest: str = "dados/bancos.csv", fontes_dir: str = "dados/fontes_bancos"):
    """
    Agrega vários CSVs de fontes locais em um único bancos.csv.
    - Lê todos *.csv em dados/fontes_bancos/
    - Detecta separador (vírgula/ponto-e-vírgula) e encoding (utf-8; fallback latin1)
    - Normaliza colunas e modalidade (SAC, SAC_TR, SAC_IPCA)
    - Gera 'Oferta' = "<Banco> — <Modalidade bonitinha>"
    Fallback: se não houver arquivos, usa template ou cria mínimo.
    """
    src_dir = Path(fontes_dir)
    dest_p = Path(dest); dest_p.parent.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(src_dir.glob("*.csv"))

    if not arquivos:
        # Fallback antigo (template/minimal)
        template = Path("dados/_templates/bancos.template.csv")
        if template.exists():
            dest_p.write_bytes(template.read_bytes())
            logger.warning("Fallback aplicado (template) → %s", dest_p)
            return str(dest_p), "Template aplicado (fallback)."
        minimo = "Oferta,Tipo\nBanco A — SAC,SAC\nBanco B — SAC TR,SAC_TR\nBanco C — SAC IPCA+,SAC_IPCA\n"
        dest_p.write_text(minimo, encoding="utf-8")
        logger.warning("Fallback aplicado (mínimo gerado) → %s", dest_p)
        return str(dest_p), "CSV mínimo criado (fallback)."

    frames = []
    for f in arquivos:
        # tenta utf-8; fallback latin1
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

        # detecta separador
        sep = ";" if txt.count(";") > txt.count(",") else ","
        df = pd.read_csv(StringIO(txt), sep=sep, engine="python")

        # normaliza nomes de colunas
        def _norm_col(c: str) -> str:
            c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode("ascii")
            c = c.strip().lower().replace("-", "_").replace(" ", "_")
            return c

        df.columns = [_norm_col(c) for c in df.columns]

        def pick(*cands):
            for c in cands:
                if c in df.columns:
                    return df[c].astype(str)
            return pd.Series([""] * len(df))

        banco = pick("banco", "instituicao", "instituicao_financeira", "origem", "oferta", "nome")
        tipo_raw = pick("tipo", "modalidade", "produto", "linha", "modalidade_financiamento")

        # se vazio, tenta deduzir a partir do nome do arquivo
        tipo_raw = tipo_raw.replace("", f.stem)

        def norm_tipo(s: str) -> str | None:
            s = (s or "").upper().replace("_", "-")
            if "IPCA" in s:
                return "SAC_IPCA"
            if "SAC" in s and "TR" in s:
                return "SAC_TR"
            if "SAC" in s:
                return "SAC"
            return None

        tipo = tipo_raw.map(norm_tipo)
        ok = tipo.notna()
        if ok.sum() == 0:
            logger.warning("Sem modalidade reconhecida: %s (ignorado)", f)
            continue

        def oferta_label(b, t):
            t_disp = {"SAC": "SAC", "SAC_TR": "SAC TR", "SAC_IPCA": "SAC IPCA+"}.get(t, t)
            b = str(b).strip()
            return f"{b} — {t_disp}" if b else t_disp

        out = pd.DataFrame({
            "Oferta": [oferta_label(b, t) for b, t in zip(banco[ok], tipo[ok])],
            "Tipo": tipo[ok].values
        })

        # mantém colunas extras úteis
        extras = [c for c in df.columns if c not in {
            "oferta","tipo","modalidade","produto","linha",
            "banco","instituicao","instituicao_financeira","origem","nome"
        }]
        out = pd.concat([out.reset_index(drop=True),
                         df.loc[ok, extras].reset_index(drop=True)], axis=1)
        frames.append(out)

    if not frames:
        logger.warning("Nenhum arquivo válido agregado; caindo em fallback mínimo.")
        dest_p.write_text("Oferta,Tipo\nBanco A — SAC,SAC\n", encoding="utf-8")
        return str(dest_p), "Nenhuma fonte válida; mínimo gerado."

    final = pd.concat(frames, ignore_index=True)
    final = final.drop_duplicates(subset=["Oferta"], keep="first")
    final.to_csv(dest_p, index=False, encoding="utf-8")
    logger.info("Agregado %d arquivos → %s (%d linhas)", len(arquivos), dest_p, len(final))
    return str(dest_p), f"Agregado {len(arquivos)} arquivo(s)."
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
        caminho, msgupd = atualizar_bancos_csv(dest=fontes.caminho_bancos)
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

run = st.button("Executar comparação")

if run:
    # Contrato do controlador preservado
    fonte_ipca = {"caminho_ipca": fontes.caminho_ipca}
    fonte_tr   = {"fixture_csv_path": fontes.caminho_tr_compat}

    logger.info(
        "Executando simulação | valor_total=%.2f, entrada=%.2f, prazo_anos=%d, taxa_juros_anual=%.4f",
        fin.valor_total, fin.entrada, fin.prazo_anos, fin.taxa_juros_anual
    )

    resultados, ranking, msg = ControladorApp().simular_multiplos_bancos(
        caminho_bancos_csv=fontes.caminho_bancos,
        dados_financiamento={
            "valor_total": fin.valor_total,
            "entrada": fin.entrada,
            "prazo_anos": fin.prazo_anos,
            "taxa_juros_anual": fin.taxa_juros_anual,
        },
        fonte_ipca=fonte_ipca,
        fonte_tr=fonte_tr,
    )

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
