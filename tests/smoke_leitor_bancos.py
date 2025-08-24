import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from infrastructure.data.leitor_bancos import carregar_bancos_csv

bancos = carregar_bancos_csv(os.path.join('dados', 'bancos.csv'))
print(f"Linhas: {len(bancos)}")
for b in bancos:
    print(b)
