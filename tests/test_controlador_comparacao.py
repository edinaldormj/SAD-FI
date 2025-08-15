import os
import sys

# Ajusta o path para src/
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from application.controlador import ControladorApp

def testar_comparador_via_controlador():
    print("🔧 Iniciando teste de comparação via ControladorApp")

    dados_sac = {
        "valor_total": 300000,
        "entrada": 50000,
        "prazo_anos": 5,
        "sistema": "SAC",
        "taxa_juros_anual": 0.0617  # ~0.5% ao mês
    }

    dados_ipca = {
        "valor_total": 300000,
        "entrada": 50000,
        "prazo_anos": 5,
        "sistema": "SAC_IPCA",
        "caminho_ipca": "dados/ipca_fixo.csv",  # 0,5% ao mês
        "taxa_juros_anual": 0.0617  # ~0,5% a.m. equivalente; use 0.12 se quiser 12% a.a.
    }

    app = ControladorApp()
    resultado_sac = app.executar_simulacao(dados_sac)
    resultado_ipca = app.executar_simulacao(dados_ipca)

    print("📊 Resultado SAC fixo:", resultado_sac)
    print("📊 Resultado SAC IPCA:", resultado_ipca)

    mensagem = app.comparar_modalidades(resultado_sac, resultado_ipca)
    print("📣 Mensagem da comparação:", mensagem)

    assert "mesmo custo total" in mensagem.lower() or "vantajosa" in mensagem.lower()

    print("✅ Teste de comparação via controlador passou.")

if __name__ == "__main__":
    testar_comparador_via_controlador()
