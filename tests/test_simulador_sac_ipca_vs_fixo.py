import sys
import os

# Ajuste do path para src/
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from domain.financiamento import Financiamento
from domain.simulador_sac import SimuladorSAC
from domain.simulador_sac_ipca import SimuladorSAC_IPCA
from infrastructure.data.tabela_ipca import TabelaIPCA
import pandas as pd

def criar_tabela_ipca_fixa(valor_percentual, meses):
    """
    Cria DataFrame com IPCA fixo (ex: 0,50%) para N meses.
    """
    data = {
        "data": [f"01/{2024 + i//12}" for i in range(meses)],
        "ipca": [valor_percentual] * meses
    }
    return pd.DataFrame(data)

def testar_ipca_fixo_equivalente_juros_fixo():
    prazo_anos = 5
    meses = prazo_anos * 12
    ipca_mensal_percentual = 0.50  # 0,50% ao mês

    # Cria financiamento comum
    financiamento = Financiamento(valor_total=300000, entrada=50000, prazo_anos=prazo_anos, sistema="SAC")

    # Simulador com taxa fixa anual equivalente a 0,50% ao mês (~6,17% a.a.)
    taxa_anual_equivalente = (1 + 0.005) ** 12 - 1
    sac_fixo = SimuladorSAC(financiamento, taxa_anual_equivalente)
    resultado_fixo = sac_fixo.simular()

    # Simulador com IPCA fixo de 0,50%
    tabela_ipca_df = criar_tabela_ipca_fixa(ipca_mensal_percentual, meses)
    tabela_ipca_df.to_csv("dados/ipca_fixo.csv", sep=";", index=False)

    sac_ipca = SimuladorSAC_IPCA(financiamento, TabelaIPCA("dados/ipca_fixo.csv"))
    resultado_ipca = sac_ipca.simular()

    print("💸 Total SAC fixo:", resultado_fixo.total_pago)
    print("💸 Total SAC IPCA:", resultado_ipca.total_pago)
    print("📉 Diferença absoluta:", abs(resultado_fixo.total_pago - resultado_ipca.total_pago))

    assert abs(resultado_fixo.total_pago - resultado_ipca.total_pago) < 10.0
    print("✅ Teste passou: os simuladores produzem valores coerentes com IPCA fixo.")

if __name__ == "__main__":
    testar_ipca_fixo_equivalente_juros_fixo()
