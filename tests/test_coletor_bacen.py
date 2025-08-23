"""
Teste do coletor_bacen.obter_ipca_df usando fixture_csv_path (modo offline).
Valida:
- DataFrame retornado contém colunas 'data' e 'ipca'
- TabelaIPCA.from_dataframe consome sem erro
"""

import os, sys, tempfile
import pandas as pd

# garante que src/ esteja no sys.path
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from infrastructure.data.coletor_bacen import obter_ipca_df
from infrastructure.data.tabela_ipca import TabelaIPCA


def testar_coletor_fixture():
    print("\n🔧 testar_coletor_fixture (fixture_csv_path)")

    # cria CSV temporário com 6 meses de IPCA em %
    content = """data,ipca
2024-01,0.5
2024-02,0.4
2024-03,0.6
2024-04,0.3
2024-05,0.45
2024-06,0.35
"""
    with tempfile.TemporaryDirectory() as tmp:
        fixture_path = os.path.join(tmp, "ipca_fixture.csv")
        with open(fixture_path, "w", encoding="utf-8") as f:
            f.write(content)

        df = obter_ipca_df(fixture_csv_path=fixture_path)
        print("DataFrame retornado:", df.head())

        # checagens básicas
        assert "data" in df.columns
        assert "ipca" in df.columns
        assert len(df) == 6

        # consumir via TabelaIPCA
        tabela = TabelaIPCA.from_dataframe(df)
        v1 = tabela.get_ipca(1)
        print("IPCA fração mês1:", v1)
        # CSV tinha 0.5% → get_ipca deve retornar 0.005
        assert abs(v1 - 0.005) < 1e-9


if __name__ == "__main__":
    testar_coletor_fixture()
    print("\n🎯 Teste coletor_bacen (fixture_csv_path) passou.")
