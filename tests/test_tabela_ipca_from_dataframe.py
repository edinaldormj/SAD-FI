import os, sys
import pandas as pd

# garantir src no path
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from infrastructure.data.tabela_ipca import TabelaIPCA

def testar_from_dataframe_com_percentual():
    print("\n🔧 testar_from_dataframe_com_percentual")
    # valores em percentual (ex.: 0.5% = 0.5)
    df = pd.DataFrame({"data": ["2024-01-01", "2024-02-01"], "ipca": [0.5, 0.4]})
    tabela = TabelaIPCA.from_dataframe(df)
    # get_ipca retorna fração (0.5% -> 0.005)
    v1 = tabela.get_ipca(1)
    v2 = tabela.get_ipca(2)
    print("ipca fração mês1:", v1, "mês2:", v2)
    assert abs(v1 - 0.005) < 1e-9
    assert abs(v2 - 0.004) < 1e-9

def testar_from_dataframe_com_fracao():
    print("\n🔧 testar_from_dataframe_com_fracao")
    # valores em fração (ex.: 0.005 = 0.5%)
    df = pd.DataFrame({"data": ["01/2024", "02/2024"], "ipca": [0.005, 0.004]})
    tabela = TabelaIPCA.from_dataframe(df)
    v1 = tabela.get_ipca(1)
    v2 = tabela.get_ipca(2)
    print("ipca fração mês1:", v1, "mês2:", v2)
    assert abs(v1 - 0.005) < 1e-9
    assert abs(v2 - 0.004) < 1e-9

if __name__ == "__main__":
    testar_from_dataframe_com_percentual()
    testar_from_dataframe_com_fracao()
    print("\n🎯 Todos os testes from_dataframe passaram.")
