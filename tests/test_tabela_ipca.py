import os
import sys

# Adiciona o diretório 'src/' ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from infrastructure.data.tabela_ipca import TabelaIPCA

print("🔧 Iniciando testes da classe TabelaIPCA")

# 🧪 Teste 1 – Leitura do arquivo (a lógica será testada depois)
print("📊 Teste 1 – Instanciação da TabelaIPCA com caminho fictício")
try:
    tabela = TabelaIPCA("dados/ipca.csv")  # Caminho real ou mock
    print("✅ Instância criada com sucesso")
except Exception as e:
    print(f"❌ Erro ao instanciar TabelaIPCA: {e}")
    assert False

# 🧪 Teste 2 – Chamada do método get_ipca (ainda sem retorno real)
print("📊 Teste 2 – Chamada do método get_ipca")
try:
    resultado = tabela.get_ipca(1)  # Stub; deve retornar None ou lançar NotImplemented
    print("⚠️ Resultado retornado (stub):", resultado)
except NotImplementedError:
    print("ℹ️ Método ainda não implementado")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    assert False

print("✅ Stub de testes para TabelaIPCA finalizado")
