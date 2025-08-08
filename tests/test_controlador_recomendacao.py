import os
import sys

# Ajusta o path para src/
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from application.controlador import ControladorApp

def testar_recomendacao_final():
    print("🔧 Iniciando teste completo de recomendação via ControladorApp")

    # Dados simulados para SAC fixo
    dados_sac = {
        "valor_total": 300000,
        "entrada": 50000,
        "prazo_anos": 5,
        "sistema": "SAC",
        "taxa_juros_anual": 0.0617  # Aproximadamente 0,5% ao mês
    }

    # Dados simulados para SAC IPCA (IPCA fixo de 0,5%)
    dados_ipca = {
        "valor_total": 300000,
        "entrada": 50000,
        "prazo_anos": 5,
        "sistema": "SAC_IPCA",
        "caminho_ipca": "dados/ipca_fixo.csv"
    }

    app = ControladorApp()

    resultado_sac = app.executar_simulacao(dados_sac)
    resultado_ipca = app.executar_simulacao(dados_ipca)

    mensagem = app.comparar_modalidades(resultado_sac, resultado_ipca)
    print("📣 Mensagem da comparação:", mensagem)

    recomendacao = app.obter_recomendacao(mensagem)
    print("💡 Recomendação final:", recomendacao)

    assert "Recomendado" in recomendacao or "Nenhuma recomendação" in recomendacao

    print("✅ Teste de recomendação final passou com sucesso.")

if __name__ == "__main__":
    testar_recomendacao_final()
