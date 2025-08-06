import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from domain.financiamento import Financiamento
from domain.simulador_sac import SimuladorSAC
from domain.parcela import Parcela

print("🔧 Iniciando teste de SimuladorSAC")

# 🔢 Dados do financiamento
financiamento = Financiamento(
    valor_total=100000.00,
    entrada=20000.00,
    prazo_anos=1,        # 12 meses
    sistema='SAC'
)

taxa_juros_anual = 0.12  # 12% ao ano

# 🧠 Esperados (cálculo manual ou verificado)
valor_financiado = financiamento.valor_financiado()     # 80.000
prazo_meses = financiamento.prazo_meses                 # 12
amortizacao = valor_financiado / prazo_meses            # 6666.67
taxa_juros_mensal = (1 + taxa_juros_anual) ** (1/12) - 1
saldo_inicial = valor_financiado
juros_1a_parcela = saldo_inicial * taxa_juros_mensal
valor_1a_parcela = amortizacao + juros_1a_parcela

# 🧪 Executando simulação
simulador = SimuladorSAC(financiamento, taxa_juros_anual)
parcelas = simulador.simular()

# ✅ Teste 1 – Verifica número de parcelas
print("📊 Teste 1 – Número de parcelas:", len(parcelas))
assert len(parcelas) == 12

# ✅ Teste 2 – Verifica valores da primeira parcela
p1 = parcelas[0]
print("📊 Teste 2 – Primeira parcela:", p1)
assert abs(p1.amortizacao - amortizacao) < 1e-2
assert abs(p1.juros - juros_1a_parcela) < 1e-2
assert abs(p1.valor_total - valor_1a_parcela) < 1e-2
assert abs(p1.saldo_devedor - saldo_inicial) < 1e-2

# ✅ Teste 3 – Verifica se saldo final é aproximadamente zero
saldo_final = parcelas[-1].saldo_devedor - amortizacao
print("📊 Teste 3 – Saldo final aproximado:", saldo_final)
assert abs(saldo_final) < 1e-2

print("\n📊 Validação da consistência dos dados gerados")

# 1. Soma das amortizações
soma_amortizacoes = sum(p.amortizacao for p in parcelas)
assert abs(soma_amortizacoes - valor_financiado) < 1e-2, "❌ Erro na soma das amortizações"

# 2. Soma dos valores totais pagos
soma_valor_total = sum(p.valor_total for p in parcelas)
print(f"💰 Total pago ao longo do financiamento: R$ {soma_valor_total:.2f}")

# 3. Verificação do saldo final
saldo_estimado_final = parcelas[-1].saldo_devedor - amortizacao
assert abs(saldo_estimado_final) < 1e-2, "❌ Saldo final não está zerando corretamente"

# 4. Parcelas decrescentes
parcelas_totais = [p.valor_total for p in parcelas]
decrescente = all(parcelas_totais[i] >= parcelas_totais[i+1] for i in range(len(parcelas_totais) - 1))
assert decrescente, "❌ Parcelas não estão decrescendo (característica do SAC)"

print("✅ Validação da consistência passou com sucesso!")
input("Pressione Enter para sair...")


print("\n\n✅ Todos os testes para SimuladorSAC passaram com sucesso!")
input("Pressione Enter para sair...")
