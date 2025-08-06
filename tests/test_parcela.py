import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from domain.parcela import Parcela

print("🔧 Iniciando testes da classe Parcela")

# 🧪 Caso 1 – Instância correta
parcela1 = Parcela(1, 1000.00, 500.00, 1500.00, 90000.00)
esperado1 = Parcela(1, 1000.00, 500.00, 1500.00, 90000.00)
print("📊 Teste 1 – Valores exatos:", parcela1)
assert parcela1 == esperado1

# 🧪 Caso 2 – Variação decimal pequena (tolerância)
parcela2 = Parcela(1, 1000.0000001, 500.0, 1500.0, 90000.0)
print("📊 Teste 2 – Diferença decimal pequena:", parcela2)
assert parcela2 == esperado1, "❌ Tolerância numérica falhou"

# 🧪 Caso 3 – Comparação com tipo errado
nao_parcela = "não sou parcela"
print("📊 Teste 3 – Comparação com tipo inválido:", nao_parcela)
assert parcela1 != nao_parcela, "❌ Comparação com tipo errado deve retornar False"

# 🧪 Caso 4 – Valores negativos
parcela_negativa = Parcela(2, -1000.00, -500.00, -1500.00, -90000.00)
print("📊 Teste 4 – Valores negativos:", parcela_negativa)
assert parcela_negativa == Parcela(2, -1000.00, -500.00, -1500.00, -90000.00)

# 🧪 Caso 5 – Valores zero
parcela_zero = Parcela(3, 0.00, 0.00, 0.00, 0.00)
print("📊 Teste 5 – Valores zero:", parcela_zero)
assert parcela_zero == Parcela(3, 0.00, 0.00, 0.00, 0.00)

print("✅ Todos os testes passaram com sucesso!")
input("Pressione Enter para sair...")

