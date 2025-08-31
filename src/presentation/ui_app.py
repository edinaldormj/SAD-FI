import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import streamlit as st

from application.controlador import ControladorApp
from presentation.ui_state import FinanciamentoInput, FontesInput
from presentation.formatters import brl

st.set_page_config(page_title="SAD-FI — Comparador", layout="wide")
st.title("SAD-FI — Comparador de Financiamentos (SAC, SAC TR, SAC IPCA)")

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
        caminho_bancos=st.text_input("bancos.csv", "dados/bancos.csv"),
        caminho_ipca=st.text_input("IPCA (CSV Bacen)", "dados/txjuros/IPCA_BACEN.csv"),
        caminho_tr_compat=st.text_input("TR (mensal compat.)", "dados/txjuros/TR_mensal_compat.csv"),
    )

run = st.button("Executar comparação")

if run:
    # Contrato do controlador (Seção 3) preservado
    fonte_ipca = {"caminho_ipca": fontes.caminho_ipca}
    fonte_tr   = {"fixture_csv_path": fontes.caminho_tr_compat}
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

    st.info(msg)

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

    st.subheader("Evolução do valor da parcela — Top 3")
    top3 = ranking[:3]
    fig = plt.figure(figsize=(10, 5))
    for rotulo, _ in top3:
        x, y = _serie_parcelas(resultados[rotulo])
        plt.plot(x, y, linewidth=2, label=rotulo)
    if top3:
        n = max(len(_serie_parcelas(resultados[r])[0]) for r, _ in top3)
        anos = list(range(12, n + 1, 12))
        if anos:
            plt.xticks(anos)
    plt.xlabel("Parcela (marcas anuais)")
    plt.ylabel("Valor (R$)")
    plt.title("Top 3 — Evolução das parcelas")
    plt.grid(True, alpha=0.25)
    plt.legend()
    st.pyplot(fig)

    # Export rápido
    out_dir = Path("resultados"); out_dir.mkdir(exist_ok=True)
    df_rank.to_csv(out_dir / "ranking.csv", index=False, encoding="utf-8")
    st.caption(f"CSV salvo em: {out_dir/'ranking.csv'}")
