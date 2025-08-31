from application.controlador import ControladorApp

def test_e2e_offline_minimo():
    resultados, ranking, _ = ControladorApp().simular_multiplos_bancos(
        caminho_bancos_csv="dados/bancos.csv",
        dados_financiamento={
            "valor_total": 300_000.0,
            "entrada": 60_000.0,
            "prazo_anos": 30,
            "taxa_juros_anual": 0.11,
        },
        fonte_ipca={"caminho_ipca": "dados/txjuros/IPCA_BACEN.csv"},
        fonte_tr={"fixture_csv_path": "dados/txjuros/TR_mensal_compat.csv"},
    )
    assert len(ranking) > 0
    assert min(tp for _, tp in ranking) > 0
    # quando bancos.csv tiver as três modalidades, validar presença:
    sistemas = {lbl.split(" — ")[-1] if "—" in lbl else lbl for lbl, _ in ranking}
    esperado = {"SAC", "SAC_TR", "SAC_IPCA"}
    assert esperado.intersection(sistemas)  # pelo menos uma presente
