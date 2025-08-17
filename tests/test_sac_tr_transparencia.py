import os
import sys

# Garante que src/ esteja no sys.path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from domain.simulador_sac import SimuladorSAC
from domain.financiamento import Financiamento
from domain.simulacao_resultado import SimulacaoResultado

def quase_igual(valor1, valor2, tol=1e-6):
    return abs(valor1 - valor2) < tol

def imprimir_resumo(resultado, titulo, correcao_tr_acumulada):
    print(f"\n📊 {titulo}")
    print(f"Parcelas: {len(resultado.parcelas)}")
    print(f"Total pago: {resultado.total_pago:,.2f}")
    print(f"Total juros: {resultado.total_juros:,.2f}")
    print(f"Saldo final: {resultado.parcelas[-1].saldo_devedor:.10f}")
    valor_financiado = resultado.parcelas[0].saldo_devedor
    soma_amortizacoes = sum(p.amortizacao for p in resultado.parcelas)
    print(f"Resumo financeiro: valor_financiado={valor_financiado:.2f}, "
          f"soma_amortizacoes={soma_amortizacoes:.2f}, "
          f"correcao_tr_acumulada={correcao_tr_acumulada:.2f}")

def testar_tr_zero_equivalente():
    print("\n🔧 Transparência: TR = 0 deve ser equivalente ao SAC atual")

    financiamento = Financiamento(120000, 24000, 2, "SAC", taxa_juros_anual=0.06)

    # Sem TR
    r_sem_tr = SimuladorSAC(financiamento, financiamento.taxa_juros_anual).simular()

    # Com TR=0
    r_com_tr_zero = SimuladorSAC(financiamento, financiamento.taxa_juros_anual).simular(tr_mensal=0.0, usar_tr=True)

    correcao_tr_acumulada = 0.0  # TR zero

    imprimir_resumo(r_sem_tr, "SAC sem TR", correcao_tr_acumulada)
    imprimir_resumo(r_com_tr_zero, "SAC com TR=0", correcao_tr_acumulada)

    # Ambos devem ter saldo final ≈ 0
    assert quase_igual(r_sem_tr.parcelas[-1].saldo_devedor, 0.0)
    assert quase_igual(r_com_tr_zero.parcelas[-1].saldo_devedor, 0.0)
    # Totais devem ser iguais
    assert quase_igual(r_sem_tr.total_pago, r_com_tr_zero.total_pago)
    assert quase_igual(r_sem_tr.total_juros, r_com_tr_zero.total_juros)

def testar_tr_positiva_transparencia():
    print("\n🔧 Transparência: TR positiva deve elevar correção do principal e custo total")

    financiamento = Financiamento(180000, 42500, 1, "SAC", taxa_juros_anual=0.05)

    tr_mensal = 0.001  # 0,1% a.m.

    # Sem TR
    r_sem_tr = SimuladorSAC(financiamento, financiamento.taxa_juros_anual).simular()

    # Com TR positiva
    r_com_tr = SimuladorSAC(financiamento, financiamento.taxa_juros_anual).simular(tr_mensal=tr_mensal, usar_tr=True)

    # Cálculo da correção acumulada teórica (simplificado para TR constante)
    saldo = financiamento.valor_financiado()
    correcao_total = 0.0
    amortizacao_const = saldo / financiamento.prazo_meses
    for _ in range(financiamento.prazo_meses):
        saldo_corrigido = saldo * (1 + tr_mensal)
        correcao_total += saldo_corrigido - saldo
        saldo = saldo_corrigido - amortizacao_const

    imprimir_resumo(r_sem_tr, "SAC sem TR", correcao_total)
    imprimir_resumo(r_com_tr, f"SAC com TR={tr_mensal*100:.3f}% a.m.", correcao_total)

    # Validações
    # 1) Custo total e juros devem aumentar com TR positiva
    assert r_com_tr.total_pago > r_sem_tr.total_pago, "Custo total deveria ser maior com TR positiva"
    assert r_com_tr.total_juros > r_sem_tr.total_juros, "Juros totais deveriam ser maiores com TR positiva"

    # 2) Saldo final deve ser ~0 (há quitação no último mês no SAC+TR)
    assert abs(r_com_tr.parcelas[-1].saldo_devedor - 0.0) < 1e-6, "Saldo final deve ser zero com quitação"
    
    # 3) Verificar a regra de quitação: amortização da última parcela ≈ saldo_corrigido
    p_ult = r_com_tr.parcelas[-1]
    # Como você salva os campos de transparência nas parcelas:
    # saldo_anterior -> saldo antes da TR; saldo_corrigido -> saldo após TR no mês
    assert hasattr(p_ult, "saldo_corrigido")
    assert abs(p_ult.amortizacao - p_ult.saldo_corrigido) < 1e-6, \
        "No último mês com TR, a amortização deve quitar o saldo corrigido"

    # 4) Conferir a métrica de transparência no resultado
    rf = r_com_tr.resumo_financeiro()  # usa soma_amortizacoes - valor_financiado
    assert rf["correcao_tr_acumulada"] > 0.0, "Deveria haver correção acumulada com TR positiva"

if __name__ == "__main__":
    testar_tr_zero_equivalente()
    testar_tr_positiva_transparencia()
    print("\n🎯 Todos os testes de transparência da TR no SAC passaram com sucesso!")
