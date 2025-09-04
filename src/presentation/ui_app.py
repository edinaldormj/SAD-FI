# --- bootstrap: inclui 'src' no sys.path ------------------------------------
import sys
from pathlib import Path
SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
# ---------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import requests
from application.controlador import ControladorApp
from presentation.ui_state import FinanciamentoInput, FontesInput
from presentation.formatters import brl
from matplotlib.ticker import FuncFormatter

# helpers modulares
from presentation.logging_setup import logger, file_stat
from presentation.io_utils import save_upload
from presentation.bancos_aggregador import agregar_bancos_csv
from presentation.bancos_schema_fix import parse_missing_from_error, ensure_bancos_schema
from presentation.plots import plot_ranking, plot_top3, save_fig_png

st.set_page_config(page_title="SAD-FI — Comparador", layout="wide")
st.title("SAD-FI — Comparador de Financiamentos (SAC, SAC-TR, SAC+IPCA)")

# ----- Inputs ----------------------------------------------------------------
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

    # Uploads opcionais (salvam no caminho atual)
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

    # Agregar bancos.csv a partir de dados/fontes_bancos (com taxa default da UI)
    if st.button("Atualizar bancos.csv (agregar fontes locais)"):
        caminho, msgupd = agregar_bancos_csv(
            dest=fontes.caminho_bancos,
            fontes_dir="dados/fontes_bancos",
            taxa_default=fin.taxa_juros_anual,
        )
        fontes.caminho_bancos = caminho
        st.info(msgupd)
        st.success(f"bancos.csv atualizado em: {caminho}")

st.caption(f"Usando bancos: {fontes.caminho_bancos} | IPCA: {fontes.caminho_ipca} | TR: {fontes.caminho_tr_compat}")
logger.info("Fontes | bancos=%s | IPCA=%s | TR=%s",
            file_stat(fontes.caminho_bancos), file_stat(fontes.caminho_ipca), file_stat(fontes.caminho_tr_compat))

# ----- Execução --------------------------------------------------------------
run = st.button("Executar comparação")

if run:
    logger.info("Exec | valor_total=%.2f, entrada=%.2f, prazo_anos=%d, taxa_juros_anual=%.4f",
                fin.valor_total, fin.entrada, fin.prazo_anos, fin.taxa_juros_anual)

    controlador = ControladorApp()

    # Função utilitária para chamar a simulação (evita duplicar código)
    def _call_simulation():
        return controlador.simular_multiplos_bancos(
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

    try:
        # Exibe spinner durante a simulação
        with st.spinner("Simulação em andamento… isso pode levar alguns minutos."):
            resultados, ranking, msg = _call_simulation()

    except requests.RequestException:
        # Falha de rede ao acessar BACEN / fonte online
        st.error("Não foi possível acessar a fonte online (BACEN). Tente novamente mais tarde ou carregue um CSV local de IPCA/TR.")
        logger.exception("Falha de rede ao coletar dados online.")
        resultados = ranking = msg = None

    except FileNotFoundError as e:
        st.error(f"Arquivo não encontrado: {e}")
        logger.exception("Arquivo não encontrado durante a simulação.")
        resultados = ranking = msg = None

    except ValueError as e:
        # Possível schema faltando em bancos.csv — tentamos o autofix e reexecução
        missing = parse_missing_from_error(str(e))
        if missing:
            st.info("Detectado problema no schema de bancos. Tentando aplicar correção automática e reexecutar...")
            try:
                ensure_bancos_schema(fontes.caminho_bancos, missing, fin.taxa_juros_anual)
                with st.spinner("Aplicando correção e reexecutando a simulação..."):
                    resultados, ranking, msg = _call_simulation()
            except Exception as e2:
                st.error(f"Falha ao aplicar correção automática ou reexecutar a simulação: {e2}")
                logger.exception("Erro durante autofix e reexecucao")
                resultados = ranking = msg = None
        else:
            st.error(f"Erro durante leitura/validação: {e}")
            logger.exception("ValueError durante a simulação")
            resultados = ranking = msg = None

    except KeyError as e:
        # Exemplos: fonte não informada etc.
        s = str(e)
        if "Fonte do IPCA" in s or "caminho_ipca" in s:
            st.error("Escolha uma fonte de IPCA: CSV local ou BACEN (série 433).")
        else:
            st.error(f"Erro de configuração: {e}")
        logger.exception("KeyError durante a simulação")
        resultados = ranking = msg = None

    except Exception as e:
        # Erro inesperado — não vaza stacktrace para o usuário
        logger.exception("Erro inesperado durante a simulacao")
        st.error("Erro inesperado durante a simulação. Consulte os logs para detalhes.")
        resultados = ranking = msg = None

    # Se a simulação obteve resultados, seguimos com export/exibição
    if resultados is not None and ranking is not None:
        # Tabela e export CSV
        st.subheader("Ranking")
        df_rank = pd.DataFrame(ranking, columns=["Oferta", "Total Pago"])
        st.dataframe(df_rank.style.format({"Total Pago": brl}), use_container_width=True)

        out_dir = Path("resultados"); out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "ranking.csv").write_text(df_rank.to_csv(index=False, encoding="utf-8"), encoding="utf-8")
        st.caption(f"CSV salvo em: {out_dir/'ranking.csv'}")
        logger.info("Salvo: %s", (out_dir/"ranking.csv").resolve())

        st.info(msg)

        # Gráfico Ranking (salvar antes de exibir)
        st.subheader("Ranking — Total Pago")
        fig_r = plot_ranking(df_rank, fmt_axis=FuncFormatter(lambda x,_: "R$ " + f"{x:,.0f}".replace(",", "X").replace(".", ",").replace("X",".")))
        out_g = out_dir / "graficos"; out_g.mkdir(parents=True, exist_ok=True)
        save_fig_png(fig_r, out_g / "ranking.png")
        st.caption(f"PNG salvo em: {out_g/'ranking.png'}")
        st.pyplot(fig_r, clear_figure=False)
        logger.info("Salvo: %s", (out_g/"ranking.png").resolve())

        # Gráfico Top-3
        st.subheader("Evolução do valor da parcela — Top 3")
        fig_t3 = plot_top3(resultados, ranking[:3])
        st.pyplot(fig_t3, clear_figure=True)
    else:
        # já mostramos a mensagem de erro acima; apenas não prosseguimos
        st.warning("A simulação não foi concluída devido a erros. Verifique as mensagens acima.")
