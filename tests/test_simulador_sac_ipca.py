import os
import sys

# Garante que src/ esteja no sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from domain.financiamento import Financiamento
from domain.simulador_sac_ipca import SimuladorSAC_IPCA
from infrastructure.data.tabela_ipca import TabelaIPCA

print("🔧 Iniciando testes do SimuladorSAC_IPCA")

# 🔢 Dados simulados
financiamento = Financiamento(
    valor_total=100000.00,
    entrada=20000.00,
    prazo_anos=1,        # 12 meses
    sistema='SAC-IPCA'
)

# Usa o mesmo ipca.csv usado no sistema
ipca_csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dados', 'ipca.csv'))
tabela = TabelaIPCA(ipca_csv_path)

# 🧪 Simulação
simulador = SimuladorSAC_IPCA(financiamento, tabela)
parcelas = simulador.simular()

# ✅ Teste 1 – Número de parcelas
assert len(parcelas) == 12, f"❌ Esperado 12 parcelas, obteve {len(parcelas)}"
print("📊 Parcelas geradas:", len(parcelas))

# ✅ Teste 2 – Amortização constante
amortizacao = parcelas[0].amortizacao
assert all(abs(p.amortizacao - amortizacao) < 1e-2 for p in parcelas), "❌ Amortização não é constante"
print("📊 Amortização constante verificada")

# ✅ Teste 3 – Juros variando com o tempo
juros_1 = parcelas[0].juros
juros_2 = parcelas[1].juros
assert juros_1 > juros_2, "❌ Juros não decrescem com o saldo"
print("📊 Juros decrescentes confirmados")

# ✅ Teste 4 – Saldo final próximo de zero
saldo_final = parcelas[-1].saldo_devedor - amortizacao
assert abs(saldo_final) < 1e-2, "❌ Saldo final não está zerando corretamente"
print("📊 Saldo devedor final zerado")

print("✅ Todos os testes do SimuladorSAC_IPCA passaram com sucesso!")
