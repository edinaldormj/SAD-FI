import re, unicodedata
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt

# Adicione este regex global (C1 controls: U+0080..U+009F)
_C1_RE = re.compile(r"[\u0080-\u009F]")

def _fix_text(s: str) -> str:
    """Corrige mojibake e remove caracteres de controle (C0/C1)."""
    if not isinstance(s, str):
        s = str(s)
    t = s

    # Caso clássico: UTF-8 interpretado como Latin-1 (ex.: 'SÃ£o' -> 'São')
    if "Ã" in t or "Â" in t:
        try:
            t = t.encode("latin1").decode("utf-8")
        except Exception:
            pass

    # Se houver C1, tentar reinterpretar como cp1252; se falhar, remover
    if _C1_RE.search(t):
        try:
            t = t.encode("latin1", "ignore").decode("cp1252", "ignore")
        except Exception:
            # remove qualquer C1 remanescente
            t = _C1_RE.sub("", t)

    # Normaliza e remove todos os controles C0/C1 (belt & suspenders)
    t = unicodedata.normalize("NFC", t)
    t = re.sub(r"[\u0000-\u001F\u007F-\u009F]", "", t)
    return t.strip()


def plot_ranking(df_rank, fmt_axis=None):
    # prepara dados
    df = df_rank.copy()
    df["Oferta"] = df["Oferta"].astype(str).map(_fix_text)
    df = df.sort_values("Total Pago", ascending=True).reset_index(drop=True)
    n = len(df)
    cmap = plt.get_cmap("RdYlGn_r")
    colors = [cmap(i / (n - 1) if n > 1 else 0.0) for i in range(n)]

    fig, ax = plt.subplots(figsize=(11, 0.6 * max(n, 1) + 1.2))
    bars = ax.barh(df["Oferta"], df["Total Pago"], color=colors, edgecolor="none")

    xmax = float(df["Total Pago"].max()) if n else 1.0
    if fmt_axis is None:
        fmt_axis = FuncFormatter(lambda x,_: f"{x:,.0f}")
    ax.xaxis.set_major_formatter(fmt_axis)

    ax.set_xlim(0, xmax * 1.10)
    ax.margins(x=0.02)

    need_external, max_label_chars = False, 0
    from presentation.formatters import brl
    for bar, valor in zip(bars, df["Total Pago"]):
        label = brl(valor)
        max_label_chars = max(max_label_chars, len(label))
        frac = (valor / xmax) if xmax else 0.0
        if frac >= 0.18:
            ax.text(bar.get_width() - 0.01 * xmax,
                    bar.get_y() + bar.get_height() / 2,
                    label, va="center", ha="right", fontsize=10, color="white")
        else:
            ax.text(bar.get_width() + 0.01 * xmax,
                    bar.get_y() + bar.get_height() / 2,
                    label, va="center", ha="left", fontsize=10)
            need_external = True

    if need_external:
        extra = 0.03 + 0.012 * max_label_chars
        ax.set_xlim(0, xmax * (1.0 + min(extra, 0.40)))

    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.25)
    ax.set_xlabel("Total Pago")
    ax.set_ylabel("Oferta")
    fig.tight_layout()
    fig.canvas.draw()
    return fig

def plot_top3(resultados: dict, top3, width=11, height=5):
    def _serie_parcelas(res):
        if hasattr(res, "to_dataframe"):
            try:
                df = res.to_dataframe()
                if {"n_parcela","valor_parcela"}.issubset(df.columns):
                    return df["n_parcela"].tolist(), df["valor_parcela"].tolist()
            except Exception:
                pass
        px = [getattr(p, "numero", i + 1) for i, p in enumerate(res.parcelas)]
        py = [float(p.valor_total) for p in res.parcelas]
        return px, py

    fig, ax = plt.subplots(figsize=(width, height))
    for rotulo, _ in top3:
        label = _fix_text(rotulo)
        x, y = _serie_parcelas(resultados[rotulo])
        ax.plot(x, y, linewidth=2, label=label)

    # ticks anuais (a cada 12 parcelas), com redução de densidade
    if top3:
        n = max(len(_serie_parcelas(resultados[r])[0]) for r, _ in top3)
        anos = list(range(12, n + 1, 12))
        step = 1
        if len(anos) > 24: step = 2
        if len(anos) > 36: step = 5
        ax.set_xticks(anos[::step])
        ax.set_xticklabels([f"Ano {i}" for i in range(1, len(anos) + 1)][::step])

    ax.yaxis.set_major_formatter(FuncFormatter(lambda x,_: "R$ " + f"{x:,.0f}".replace(",", "X").replace(".", ",").replace("X",".")))
    ax.set_xlabel("Tempo")
    ax.set_ylabel("Valor da parcela")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right", frameon=False)
    ax.margins(x=0)
    fig.tight_layout()
    return fig

def save_fig_png(fig, path):
    path = str(path)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
