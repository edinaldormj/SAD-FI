import os
import sys
import pandas as pd

# Garante que src/ está no path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)


from infrastructure.data.leitor_csv import ler_csv

print("🔧 Iniciando testes do leitor_csv.py")

# Caminho para o arquivo de testes (ajuste conforme necessário)
csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dados', 'ipca.csv'))

# Teste 1 – Leitura básica
try:
    df = ler_csv(csv_path)
    print("✅ Leitura bem-sucedida.")
except Exception as e:
    print(f"❌ Erro ao ler o CSV: {e}")
    assert False

# Teste 2 – Verifica colunas
esperadas = {"data", "ipca"}
obtidas = set(df.columns)
assert esperadas == obtidas, f"❌ Colunas esperadas {esperadas}, mas obtidas {obtidas}"

# Teste 3 – Verifica se IPCA é float
assert pd.api.types.is_float_dtype(df["ipca"]), "❌ Coluna 'ipca' não está como float"

# Teste 4 – Verifica se não há a linha da fonte
assert not df["data"].str.contains("Fonte", case=False).any(), "❌ Linha da fonte não foi removida"

print("✅ Todos os testes passaram com sucesso!")