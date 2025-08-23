"""
Teste de integração real com a API do BACEN (série 433 - IPCA).
- Requer internet ativa.
- Se a API estiver fora ou sem rede, este teste vai falhar.
"""

import os, sys
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from infrastructure.data.coletor_bacen import obter_ipca_df
from infrastructure.data.tabela_ipca import TabelaIPCA

def testar_coletor_bacen_online():
    print("\n🔧 testar_coletor_bacen_online (API real)")
    df = obter_ipca_df(meses=6)  # chamada real

    print("Primeiras linhas do DataFrame:\n", df.head())
    assert "data" in df.columns
    assert "ipca" in df.columns
    assert not df["ipca"].isna().any(), "Coluna ipca não deveria ter NaN"
    assert len(df) > 0, "DataFrame deveria ter pelo menos 1 linha"

    # integração com TabelaIPCA
    tabela = TabelaIPCA.from_dataframe(df)
    v1 = tabela.get_ipca(1)
    print("IPCA fração mês1:", v1)
    assert 0 <= v1 < 0.02, "IPCA (fração) deve estar em faixa plausível (<2%)"

if __name__ == "__main__":
    testar_coletor_bacen_online()
    print("\n🎯 Teste coletor_bacen_online passou (API real).")
