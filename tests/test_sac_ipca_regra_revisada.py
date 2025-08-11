import os
import sys

# Garante que src/ esteja no sys.path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from domain.simulador_sac_ipca import SimuladorSAC_IPCA
from domain.financiamento import Financiamento
from domain.simulacao_resultado import SimulacaoResultado


class TabelaIPCATeste:
    """Tabela IPCA fake para testes, com valores mensais pré-definidos."""
    def __init__(self, valores):
        self.valores = valores

    def get_ipca(self, mes):
        return self.valores[mes - 1]


def quase_igual(valor1, valor2, tol=1e-6):
    return abs(valor1 - valor2) < tol


def imprimir_resumo(resultado, titulo):
    """Mostra resumo da simulação para facilitar debug."""
    print(f"\n📊 {titulo}")
    print(f"Parcelas: {len(resultado.parcelas)}")
    print(f"Total pago: R$ {resultado.total_pago:,.2f}")
    print(f"Total juros: R$ {resultado.total_juros:,.2f}")
    print(f"Saldo final: {resultado.parcelas[-1].saldo_devedor:.10f}")
    print("Últimas 3 parcelas:")
    for p in resultado.parcelas[-3:]:
        print(f" Parcela {p.numero}: amortização={p.amortizacao:.2f}, juros={p.juros:.2f}, total={p.valor_total:.2f}, saldo={p.saldo_devedor:.10f}")


def testar_deflacao_vs_ipca_zero():
    print("\n🔧 Testando cenário de deflação vs. IPCA zero")

    financiamento = Financiamento(100000, 0, 2, "SAC_IPCA", taxa_juros_anual=0.06)

    ipca_negativo = TabelaIPCATeste([-0.005] * 24)
    resultado_negativo = SimuladorSAC_IPCA(financiamento, ipca_negativo).simular()

    ipca_zero = TabelaIPCATeste([0.0] * 24)
    resultado_zero = SimuladorSAC_IPCA(financiamento, ipca_zero).simular()

    imprimir_resumo(resultado_negativo, "Deflação -0,5% a.m.")
    imprimir_resumo(resultado_zero, "IPCA zero")

    assert quase_igual(resultado_negativo.parcelas[-1].saldo_devedor, 0.0), \
        f"Saldo final incorreto (deflação): {resultado_negativo.parcelas[-1].saldo_devedor}"
    assert quase_igual(resultado_zero.parcelas[-1].saldo_devedor, 0.0), \
        f"Saldo final incorreto (IPCA zero): {resultado_zero.parcelas[-1].saldo_devedor}"
    assert resultado_negativo.total_juros < resultado_zero.total_juros, \
        "Deflação deveria gerar juros menores"

    print("✅ Deflação vs. IPCA zero passou com sucesso!")


def testar_serie_mista_saldo_final_e_amortizacao():
    print("\n🔧 Testando série mista de IPCA e saldo final zero")

    financiamento = Financiamento(50000, 5000, 1, "SAC_IPCA", taxa_juros_anual=0.12)

    serie_mista = [0.01, -0.005, 0.0, 0.02, -0.003, 0.004, 0.0, -0.002, 0.006, -0.001, 0.005, 0.0]
    ipca_misto = TabelaIPCATeste(serie_mista)

    resultado = SimuladorSAC_IPCA(financiamento, ipca_misto).simular()

    imprimir_resumo(resultado, "Série mista IPCA")

    # ✅ Garantir saldo final próximo de zero
    assert quase_igual(resultado.parcelas[-1].saldo_devedor, 0.0), \
        f"Saldo final incorreto: {resultado.parcelas[-1].saldo_devedor}"

    # ✅ Garantir que todas as amortizações sejam positivas
    assert all(p.amortizacao > 0 for p in resultado.parcelas), \
        "Todas as amortizações devem ser positivas"

    # ✅ Garantir que houve pagamento de juros
    assert resultado.total_juros > 0, "Total de juros deveria ser positivo"

    print("✅ Série mista passou com sucesso!")



def testar_tipo_retorno():
    print("\n🔧 Testando tipo de retorno do simulador")
    financiamento = Financiamento(30000, 0, 1, "SAC_IPCA", taxa_juros_anual=0.1)
    ipca_falso = TabelaIPCATeste([0.01] * 12)
    resultado = SimuladorSAC_IPCA(financiamento, ipca_falso).simular()
    imprimir_resumo(resultado, "Tipo de retorno")
    assert isinstance(resultado, SimulacaoResultado), "Retorno não é SimulacaoResultado"
    print("✅ Tipo de retorno correto!")


if __name__ == "__main__":
    testar_deflacao_vs_ipca_zero()
    testar_serie_mista_saldo_final_e_amortizacao()
    testar_tipo_retorno()
    print("\n🎯 Todos os testes SAC+IPCA (regra revisada) passaram com sucesso!")
