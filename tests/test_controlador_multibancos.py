"""
tests/test_controlador_multibancos.py

Integração básica:
- LeitorBancos CSV (apenas SAC) -> ControladorApp.simular_multiplos_bancos -> Comparador
- Checa ordem do ranking e mensagem de recomendação.

Não usa IPCA aqui para manter o teste simples/rápido.
"""

import os
import sys
import tempfile

# garante src no path
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from application.controlador import ControladorApp

def _write_csv(tmpdir, name, text):
    p = os.path.join(tmpdir, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p

def testar_controlador_multibancos_sac_only():
    print("\n🔧 testar_controlador_multibancos_sac_only")
    # CSV de bancos (somente SAC para não depender de IPCA)
    content = """nome,sistema,taxa_anual
Banco Barato,SAC,0.10
Banco Médio,SAC,0.12
Banco Caro,SAC,0.15
"""
    with tempfile.TemporaryDirectory() as tmp:
        bancos_csv = _write_csv(tmp, "bancos_tmp.csv", content)

        ctrl = ControladorApp()

        # Dados de financiamento de exemplo
        dados_fin = {"valor_total": 300000.0, "entrada": 60000.0, "prazo_anos": 20}

        # Como não há SAC_IPCA no CSV, fonte_ipca pode ser None
        resultados, ranking, mensagem = ctrl.simular_multiplos_bancos(
            bancos_csv, dados_fin, fonte_ipca=None
        )

        print("ranking:", ranking)
        print("mensagem:", mensagem)

        # Esperado: Banco Barato (0.10) vence, seguido por Médio (0.12) e Caro (0.15)
        assert ranking[0][0].startswith("Banco Barato")
        assert ranking[1][0].startswith("Banco Médio")
        assert ranking[2][0].startswith("Banco Caro")

        # Mensagem padrão do comparador deve citar o vencedor (Banco Barato)
        assert "Recomendação:" in mensagem and "Banco Barato" in mensagem

if __name__ == "__main__":
    print("🚀 Teste integração: Controlador multi-bancos (SAC-only)")
    testar_controlador_multibancos_sac_only()
    print("🎯 OK")
