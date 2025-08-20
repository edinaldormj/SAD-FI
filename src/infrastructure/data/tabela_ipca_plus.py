"""
Extensão da TabelaIPCA: adiciona from_dataframe(df) mantendo convenção de armazenar IPCA em %.
`get_ipca(m)` segue retornando fração.
"""
from __future__ import annotations
import pandas as pd

class TabelaIPCAPlus:
    def __init__(self, df_percentual: pd.DataFrame):
        self.tabela = df_percentual.reset_index(drop=True)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> "TabelaIPCAPlus":
        df2 = df.rename(columns={"valor":"ipca"}).copy()
        assert {"data","ipca"}.issubset(df2.columns)
        # Se vier em fração, converter pra %
        if df2["ipca"].abs().max() <= 1.0:
            df2["ipca"] = df2["ipca"] * 100.0
        return cls(df2[["data","ipca"]])

    def get_ipca(self, mes: int) -> float:
        if mes < 1 or mes > len(self.tabela):
            raise IndexError(f"Mês {mes} fora do intervalo (1..{len(self.tabela)})")
        return float(self.tabela.loc[mes-1, "ipca"]) / 100.0
