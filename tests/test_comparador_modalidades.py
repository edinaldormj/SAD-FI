import os
import sys

# Ajuste do path para importar src/
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from domain.simulacao_resultado import SimulacaoResultado
from domain.parcela import Parcela
from domain.comparador import ComparadorModalidades

def criar_resultado_simulado(total, parcelas=3):
    """
    Gera um SimulacaoResultado artificial, com amortização + juros.
    """
    valor_parcela = total / parcelas
    amortizacao = valor_parcela * 0.6
    juros = valor_parcela * 0.4
    lista = [
        Parcela(i+1, amortizacao, juros, amortizacao + juros, 0)
        for i in range(parcelas)
    ]
    return SimulacaoResultado(lista)

def testar_comparador():
    comparador = ComparadorModalidades()

    # 1. Modalidade 1 mais barata
    r1 = criar_resultado_simulado(100000)
    r2 = criar_resultado_simulado(110000)
    print("🔍 r1:", r1)
    print("🔍 r2:", r2)
    msg1 = comparador.comparar(r1, r2)
    print("🧪 Teste 1 - Modalidade 1 mais barata:", msg1)
    assert "Modalidade 1 é mais vantajosa" in msg1

    # 2. Modalidade 2 mais barata
    r3 = criar_resultado_simulado(120000)
    r4 = criar_resultado_simulado(100000)
    print("🔍 r3:", r3)
    print("🔍 r4:", r4)
    msg2 = comparador.comparar(r3, r4)
    print("🧪 Teste 2 - Modalidade 2 mais barata:", msg2)
    assert "Modalidade 2 é mais vantajosa" in msg2

    # 3. Empate
    r5 = criar_resultado_simulado(115000)
    r6 = criar_resultado_simulado(115000)
    print("🔍 r5:", r5)
    print("🔍 r6:", r6)
    msg3 = comparador.comparar(r5, r6)
    print("🧪 Teste 3 - Empate:", msg3)
    assert "mesmo custo total" in msg3.lower()

    # 4. Diferença dentro da tolerância
    r7 = criar_resultado_simulado(100000.00)
    r8 = criar_resultado_simulado(100000.009)
    print("🔍 r7:", r7)
    print("🔍 r8:", r8)
    msg4 = comparador.comparar(r7, r8)
    print("🧪 Teste 4 - Diferença mínima:", msg4)
    assert "mesmo custo total" in msg4.lower()

    print("✅ Todos os testes passaram com sucesso.")

if __name__ == "__main__":
    testar_comparador()

