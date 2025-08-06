import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dominio.financiamento import Financiamento
from infra.dados.tabela_ipca import TabelaIPCA
from core.financiamento.simulador_sac_ipca import SimuladorSAC_IPCA

print("🔧 Iniciando testes de SimuladorSAC_IPCA")

# 🧪 Teste 1 – IPCA fixo: comportamento próximo ao SAC fixo
print("📊 Teste 1 – Simulação com IPCA constante (stub)")
# financiamento = Financiamento(...)
# tabela_ipca = TabelaIPCA("dados/ipca.csv")
# simulador = SimuladorSAC_IPCA(financiamento, tabela_ipca)
# resultado = simulador.simular()
# assert ...  # Verificações de parcelas e totais

# 🧪 Testes futuros: IPCA variável, saldo final, amortização constante etc.

print("✅ Stub de testes para SimuladorSAC_IPCA pronto")
