import os
import sys

# Ajusta o path para importar módulos do src/
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from application.controlador import ControladorApp

def testar_controlador_com_ipca():
    print("🔧 Iniciando teste do ControladorApp com IPCA")

    dados_entrada = {
        "valor_total": 300000,
        "entrada": 50000,
        "prazo_anos": 5,
        "sistema": "SAC_IPCA",
        "caminho_ipca": "dados/ipca_fixo.csv",
        "taxa_juros_anual": 0.0617  # ~0,5% a.m. equivalente; use 0.12 se quiser 12% a.a.

    }

    controlador = ControladorApp()
    resultado = controlador.executar_simulacao(dados_entrada)

    print("✅ Simulação realizada com sucesso.")
    print("📊 Resultado resumido:")
    print(resultado)
    print(resultado.to_dict_resumo())

if __name__ == "__main__":
    testar_controlador_com_ipca()
