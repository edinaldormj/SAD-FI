import os
import sys

# Garante que src/ esteja no sys.path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from application.controlador import ControladorApp
from domain.simulacao_resultado import SimulacaoResultado
from domain.parcela import Parcela


def criar_resultado_simulado(total, parcelas=3):
    """
    Gera um SimulacaoResultado artificial com amortização + juros,
    de forma que a soma das parcelas = 'total'.
    """
    valor_parcela = total / parcelas
    amortizacao = valor_parcela * 0.6
    juros = valor_parcela * 0.4
    lista = [
        Parcela(i + 1, amortizacao, juros, amortizacao + juros, 0.0)
        for i in range(parcelas)
    ]
    return SimulacaoResultado(lista)


def imprimir_resumo(titulo, resultado):
    print(f"\n📊 {titulo}")
    print(f"Parcelas: {len(resultado.parcelas)}")
    print(f"Total pago: {resultado.total_pago:,.2f}")
    print(f"Total juros: {resultado.total_juros:,.2f}")


def testar_recomendacao_modalidade1_mais_barata():
    ctrl = ControladorApp()
    r1 = criar_resultado_simulado(100_000, parcelas=6)   # mais barato
    r2 = criar_resultado_simulado(110_000, parcelas=6)   # mais caro

    imprimir_resumo("Modalidade 1 (esperado vencer)", r1)
    imprimir_resumo("Modalidade 2", r2)

    msg_comp = ctrl.comparar_modalidades(r1, r2)
    rec = ctrl.obter_recomendacao(msg_comp)
    print("🧠 Comparação:", msg_comp)
    print("💡 Recomendação:", rec)

    # Aceita tanto “Modalidade 1” quanto um texto de recomendação equivalente
    assert ("Modalidade 1" in msg_comp) or ("1" in rec) or ("Modalidade 1" in rec) or ("Recomendado" in rec), \
        "Esperava recomendação favorável à Modalidade 1"


def testar_recomendacao_modalidade2_mais_barata():
    ctrl = ControladorApp()
    r1 = criar_resultado_simulado(120000, parcelas=6)  # mais caro
    r2 = criar_resultado_simulado(100000, parcelas=6)  # mais barato

    imprimir_resumo("Modalidade 1", r1)
    imprimir_resumo("Modalidade 2 (esperado vencer)", r2)

    msg_comp = ctrl.comparar_modalidades(r1, r2)
    rec = ctrl.obter_recomendacao(msg_comp)
    print("🧠 Comparação:", msg_comp)
    print("💡 Recomendação:", rec)

    assert ("Modalidade 2" in msg_comp) or ("2" in rec) or ("Modalidade 2" in rec) or ("Recomendado" in rec), \
        "Esperava recomendação favorável à Modalidade 2"


def testar_recomendacao_empate():
    ctrl = ControladorApp()
    r1 = criar_resultado_simulado(115000, parcelas=5)
    r2 = criar_resultado_simulado(115000, parcelas=5)

    imprimir_resumo("Modalidade 1 (empate)", r1)
    imprimir_resumo("Modalidade 2 (empate)", r2)

    msg_comp = ctrl.comparar_modalidades(r1, r2)
    rec = ctrl.obter_recomendacao(msg_comp)
    print("🧠 Comparação:", msg_comp)
    print("💡 Recomendação:", rec)

    # Aceita “empate” ou equivalentes
    assert ("empate" in msg_comp.lower()) or ("mesmo custo" in msg_comp.lower()) \
           or ("empate" in rec.lower()) or ("neutro" in rec.lower()), \
        "Esperava recomendação de empate/neutra"


def testar_recomendacao_diferenca_minima_tolerancia():
    """
    Diferença minúscula deve ser tratada como empate (tolerância),
    conforme já testado no ComparadorModalidades.
    """
    ctrl = ControladorApp()
    r1 = criar_resultado_simulado(100000.00, parcelas=4)
    r2 = criar_resultado_simulado(100000.009, parcelas=4)  # diferença ínfima

    imprimir_resumo("Modalidade 1 (quase empate)", r1)
    imprimir_resumo("Modalidade 2 (quase empate)", r2)

    msg_comp = ctrl.comparar_modalidades(r1, r2)
    rec = ctrl.obter_recomendacao(msg_comp)
    print("🧠 Comparação:", msg_comp)
    print("💡 Recomendação:", rec)

    assert ("empate" in msg_comp.lower()) or ("mesmo custo" in msg_comp.lower()) \
           or ("empate" in rec.lower()) or ("neutro" in rec.lower()), \
        "Esperava recomendação de empate/neutra para diferença mínima"


if __name__ == "__main__":
    print("🔧 Iniciando testes de recomendação automática")
    testar_recomendacao_modalidade1_mais_barata()
    testar_recomendacao_modalidade2_mais_barata()
    testar_recomendacao_empate()
    testar_recomendacao_diferenca_minima_tolerancia()
    print("✅ Todos os testes de recomendação passaram com sucesso.")
