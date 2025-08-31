from presentation.ui_state import FinanciamentoInput, FontesInput
from application.controlador import ControladorApp

def test_smoke_ui_defaults_executa():
    fin = FinanciamentoInput()
    fontes = FontesInput()
    _, ranking, msg = ControladorApp().simular_multiplos_bancos(
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
    assert len(ranking) > 0
    assert isinstance(msg, str) and msg.strip()
