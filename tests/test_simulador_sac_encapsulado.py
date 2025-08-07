import os
import sys

# Garante que src/ esteja no sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from domain.financiamento import Financiamento
from domain.simulador_sac import SimuladorSAC
from domain.simulacao_resultado import SimulacaoResultado

print("🔧 Iniciando teste do SimuladorSAC com encapsulamento")

# 🔢 Configuração da simulação
financiamento = Financiamento(
    valor_total=100000.00,
    entrada=20000.00,
    prazo_anos=1,
    sistema='SAC'
)

taxa_anual = 0.12  # 12% ao ano

# 🧪 Execução
simulador = SimuladorSAC(financiamento, taxa_anual)
resultado = simulador.simular()

# ✅ Teste 1 – Tipo de retorno
assert isinstance(resultado, SimulacaoResultado), "❌ O retorno não é um SimulacaoResultado"
print("✅ Retorno do tipo SimulacaoResultado")

# ✅ Teste 2 – Total de parcelas
assert len(resultado.parcelas) == 12, "❌ Número de parcelas incorreto"
print("📊 Parcelas:", len(resultado.parcelas))

# ✅ Teste 3 – Total pago e total de juros coerentes
soma_valores = sum(p.valor_total for p in resultado.parcelas)
soma_juros = sum(p.juros for p in resultado.parcelas)

assert abs(soma_valores - resultado.total_pago) < 1e-2, "❌ total_pago inconsistente"
assert abs(soma_juros - resultado.total_juros) < 1e-2, "❌ total_juros inconsistente"

print(f"💰 Total pago: R$ {resultado.total_pago:.2f}")
print(f"💰 Total de juros: R$ {resultado.total_juros:.2f}")
print("✅ Todos os testes do SimuladorSAC com encapsulamento passaram com sucesso!")
