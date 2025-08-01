import sys
import os

print("🔧 Iniciando teste de Financiamento")

# Configura o path para importar de src/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
print("📁 Caminho src/ adicionado ao sys.path")

# Tenta importar Financiamento
try:
    from financiamento import Financiamento
    print("✅ Importação bem-sucedida")
except Exception as e:
    print(f"❌ Erro ao importar: {e}")
    input("Pressione Enter para sair...")
    exit(1)

# Realiza o teste
financiamento = Financiamento(valor_total=300000, entrada=60000, prazo_anos=30, sistema="SAC")
resultado = financiamento.valor_financiado()
esperado = 240000

print(f"📊 Resultado obtido: {resultado}, Esperado: {esperado}")
assert resultado == esperado, f"❌ Esperado {esperado}, mas obteve {resultado}"

print("✅ Teste passou com sucesso!")
input("Pressione Enter para sair...")
