import os
import sys

# Garante que o src/ esteja no sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from infrastructure.data.tabela_ipca import TabelaIPCA

print("🔧 Iniciando testes da classe TabelaIPCA")

# Caminho para o CSV de dados
csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dados', 'ipca.csv'))

# 🧪 Teste 1 – Instanciação e leitura
try:
    tabela = TabelaIPCA(csv_path)
    print("✅ Instância criada com sucesso")
except Exception as e:
    print(f"❌ Erro ao instanciar TabelaIPCA: {e}")
    assert False

# 🧪 Teste 2 – Retorno correto do primeiro mês
try:
    valor_mes1 = tabela.get_ipca(1)
    print(f"📊 IPCA mês 1: {valor_mes1:.6f}")
    assert isinstance(valor_mes1, float)
    assert abs(valor_mes1 - (-0.0002)) < 0.001  # Exemplo: -0,02% convertido para -0.0002
except Exception as e:
    print(f"❌ Erro ao consultar IPCA do mês 1: {e}")
    assert False

# 🧪 Teste 3 – Mês fora do intervalo
try:
    tabela.get_ipca(999)
    assert False, "❌ Esperava exceção para mês inválido, mas não houve"
except IndexError:
    print("✅ Exceção corretamente lançada para mês inválido")

print("✅ Todos os testes da TabelaIPCA passaram com sucesso!")
