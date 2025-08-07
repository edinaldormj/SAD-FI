import os
import sys

# Garante que src/ esteja no sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from domain.financiamento import Financiamento
from domain.simulador_sac_ipca import SimuladorSAC_IPCA
from infrastructure.data.tabela_ipca import TabelaIPCA
from domain.simulacao_resultado import SimulacaoResultado

print("🔧 Iniciando testes do SimuladorSAC_IPCA com encapsulamento")

# 📁 Caminho para o CSV de IPCA
csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dados', 'ipca.csv'))

# 🔢 Configuração do financiamento
financiamento = Financiamento(
    valor_total=100000.00,
    entrada=20000.00,
    prazo_anos=1,  # 12 meses
    sistema='SAC-IPCA'
)

# 📊 Leitura dos dados do IPCA
tabela = TabelaIPCA(csv_path)

# 🧪 Execução da simulação
simulador = SimuladorSAC_IPCA(financiamento, tabela)
resultado = simulador.simular()

# ✅ Teste 1 – Verifica tipo de retorno
assert isinstance(resultado, SimulacaoResultado), "❌ O retorno não é um SimulacaoResultado"
print("✅ Retorno do tipo SimulacaoResultado")

# ✅ Teste 2 – Verifica número de parcelas
assert len(resultado.parcelas) == 12, "❌ Número de parcelas incorreto"
print("📊 Parcelas:", len(resultado.parcelas))

# ✅ Teste 3 – Verifica consistência dos totais
soma_valores = sum(p.valor_total for p in resultado.parcelas)
soma_juros = sum(p.juros for p in resultado.parcelas)

assert abs(soma_valores - resultado.total_pago) < 1e-2, "❌ total_pago inconsistente"
assert abs(soma_juros - resultado.total_juros) < 1e-2, "❌ total_juros inconsistente"

# ✅ Teste 4 – Verifica saldo final próximo de zero
saldo_final = resultado.parcelas[-1].saldo_devedor - resultado.parcelas[-1].amortizacao
assert abs(saldo_final) < 1e-2, "❌ Saldo final não está zerando corretamente"

print(f"💰 Total pago: R$ {resultado.total_pago:.2f}")
print(f"💰 Total de juros: R$ {resultado.total_juros:.2f}")
print("✅ Todos os testes do SimuladorSAC_IPCA com encapsulamento passaram com sucesso!")
