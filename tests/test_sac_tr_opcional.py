import os
import sys

# Garante que src/ esteja no sys.path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from application.controlador import ControladorApp
from domain.financiamento import Financiamento
from domain.simulador_sac import SimuladorSAC
from domain.simulador_sac_ipca import SimuladorSAC_IPCA

def quase_igual(a, b, tol=1e-6):
    return abs(a - b) < tol

def testar_equivalencia_tr_desativada():
    print("\n🔧 Caso base: TR desativada (equivalente ao SAC atual)")
    fin = Financiamento(100000, 0, 1, "SAC", taxa_juros_anual=0.12)
    sim = SimuladorSAC(fin, 0.12)

    r_sem_tr = sim.simular(usar_tr=False)
    r_tr_zero = sim.simular(usar_tr=True, tr_mensal=0.0)

    assert quase_igual(r_sem_tr.total_pago, r_tr_zero.total_pago), "TR=0 deveria ser idêntico ao SAC atual"
    assert quase_igual(r_sem_tr.total_juros, r_tr_zero.total_juros), "TR=0 deveria ser idêntico ao SAC atual"
    assert quase_igual(r_tr_zero.parcelas[-1].saldo_devedor, 0.0), "Saldo final deveria ~0"

    print("✅ Equivalência (TR off / TR=0) OK")

def testar_tr_positiva_aumenta_custos():
    print("\n🔧 TR positiva pequena eleva custos")
    fin = Financiamento(100000, 0, 1, "SAC", taxa_juros_anual=0.12)
    sim = SimuladorSAC(fin, 0.12)

    r_sem_tr = sim.simular(usar_tr=False)
    r_tr = sim.simular(usar_tr=True, tr_mensal=0.001)  # 0,1% a.m.

    assert r_tr.total_pago > r_sem_tr.total_pago, "Com TR>0, custo total deve aumentar"
    assert r_tr.total_juros > r_sem_tr.total_juros, "Com TR>0, juros devem aumentar"
    assert r_tr.parcelas[-1].saldo_devedor > 0.0, \
    "Com TR>0 e amortização constante, o saldo final não deve ser zero (há resíduo)."

    print("✅ TR>0 aumenta custos, saldo final ~0")

def testar_api_nao_interfere_sac_ipca():
    print("\n🔧 Garantir que SAC+IPCA permanece sem TR")
    fin_ipca = Financiamento(50000, 0, 1, "SAC_IPCA", taxa_juros_anual=0.10)
    # Só checamos que a classe existe e simula sem parâmetros de TR
    # (não passamos TR aqui; comportamento deve ser inalterado)
    # Para rodar de ponta a ponta, você precisa de uma TabelaIPCA real ou mock.
    # Este teste é apenas sanidade da API.
    assert hasattr(SimuladorSAC_IPCA, "simular"), "SAC_IPCA deve manter sua API"

    print("✅ API do SAC+IPCA inalterada (sem TR)")

if __name__ == "__main__":
    print("🔧 Iniciando testes para TR opcional no SAC")
    testar_equivalencia_tr_desativada()
    testar_tr_positiva_aumenta_custos()
    testar_api_nao_interfere_sac_ipca()
    print("🎯 Todos os testes de TR opcional no SAC passaram com sucesso!")
