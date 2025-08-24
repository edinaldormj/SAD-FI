"""
Sugestão de paths no projeto:
- infrastructure/data/tabela_tr.py  (classe TabelaTR)
- infrastructure/coleta/coletor_tr.py (classe ColetorTR)

Este único arquivo reúne o esqueleto funcional e testes de console (prints/asserts),
seguindo o padrão já usado no projeto. Copiar/partir em arquivos conforme os paths acima.
"""
from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Tuple, Dict

# ==========================
#  TabelaTR (parse e lookup)
# ==========================
@dataclass
class TabelaTR:
    """Tabela mensal da TR normalizada em fração (ex.: 0.0012 == 0,12%)."""
    _df: pd.DataFrame
    _cache: Dict[str, float]

    @staticmethod
    def from_dataframe(df: pd.DataFrame) -> "TabelaTR":
        if df is None or df.empty:
            raise ValueError("DataFrame de TR vazio")
        df2 = df.copy()
        df2.columns = [c.strip().lower() for c in df2.columns]
        if "tr" not in df2.columns:
            if "valor" in df2.columns:
                df2.rename(columns={"valor": "tr"}, inplace=True)
            else:
                raise ValueError("Coluna 'tr' (ou 'valor') não encontrada")
        if "data" not in df2.columns:
            raise ValueError("Coluna 'data' não encontrada")

        # Normaliza datas para YYYY-MM
        d1 = pd.to_datetime(df2["data"].astype(str), format="%Y-%m", errors="coerce")
        d2 = pd.to_datetime(df2["data"].astype(str), format="%m/%Y", errors="coerce")
        d = d1.fillna(d2)
        d = d.fillna(pd.to_datetime(df2["data"].astype(str), errors="coerce"))
        if d.isna().any():
            raise ValueError("Há datas inválidas na TR")
        df2["data"] = d.dt.strftime("%Y-%m")

        # Normaliza TR para fração
        tr = pd.to_numeric(df2["tr"], errors="coerce")
        if tr.isna().any():
            raise ValueError("Valores de TR inválidos")
        if tr.abs().median() > 1.0:
            tr = tr / 100.0
        df2["tr"] = tr

        df2 = (
            df2[["data", "tr"]]
            .drop_duplicates(subset=["data"], keep="last")
            .sort_values("data")
            .reset_index(drop=True)
        )
        return TabelaTR(df2, _cache={})

    def taxa_mensal(self, ano_mes: str) -> float:
        """Retorna TR do mês (fração). Ex.: "2024-01" -> 0.0/0.0012 etc."""
        if ano_mes in self._cache:
            return self._cache[ano_mes]
        linha = self._df.loc[self._df["data"] == ano_mes]
        if linha.empty:
            raise KeyError(f"TR não encontrada para {ano_mes}")
        valor = float(linha.iloc[0]["tr"])
        self._cache[ano_mes] = valor
        return valor

    @property
    def df(self) -> pd.DataFrame:
        return self._df.copy()




# ======================================================
#  Cola de integração (Controlador & SimuladorSAC atual)
# ======================================================
INTEGRACAO_CONTROLADOR = r"""
# 1) Em ControladorApp.simular_multiplos_bancos(...), antes do loop principal,
#    materializar tabela TR uma única vez quando houver pelo menos 1 linha SAC_TR.
from infrastructure.data.tabela_tr import TabelaTR
from infrastructure.coleta.coletor_tr import ColetorTR

coletor_tr = ColetorTR(fixture_csv_path="tests/fixtures/tr_fixture.csv")  # ou online=True
_df_tr = coletor_tr.coletar()  # cache durante a simulação
_tabela_tr = TabelaTR.from_dataframe(_df_tr)

# 2) No loop de bancos/linhas do CSV:
if modalidade.upper() == "SAC_TR":
    # Opção A (se SimuladorSAC já aceita TR):
    simulador = SimuladorSAC(financiamento, taxa_juros_anual)
    resultado = simulador.simular(tr_lookup=_tabela_tr.taxa_mensal)  # adicionar parâmetro opcional

    # Opção B (se preferir classe dedicada):
    # from domain.simulador_sac_tr import SimuladorSAC_TR
    # resultado = SimuladorSAC_TR(_tabela_tr).simular(financiamento, taxa_juros_anual)
"""


# ======================
#  Testes de console (smoke)
# ======================
def _teste_tabela_from_dataframe():
    print("[TEST] TabelaTR.from_dataframe — normalização básica")
    df = pd.DataFrame({"data": ["01/2024", "2024-02", "2024-03"], "tr": [0.0, 0.04, 0.05]})
    tab = TabelaTR.from_dataframe(df)
    assert list(tab.df["data"]) == ["2024-01", "2024-02", "2024-03"]
    # 0.04 e 0.05 serão interpretados como fração se mediana <= 1.0; aqui mediana=0.04 -> fração
    assert abs(tab.taxa_mensal("2024-02") - 0.04) < 1e-12
    print("  ok")


def _teste_percentual_para_fracao():
    print("[TEST] Conversão de % para fração")
    df = pd.DataFrame({"data": ["2024-01", "2024-02"], "tr": [0.0, 0.05]})
    tab = TabelaTR.from_dataframe(df)
    assert abs(tab.taxa_mensal("2024-02") - 0.05) < 1e-12

    dfp = pd.DataFrame({"data": ["2024-01", "2024-02"], "tr": [0.0, 0.05,]})
    tabp = TabelaTR.from_dataframe(dfp)
    assert abs(tabp.taxa_mensal("2024-02") - 0.05) < 1e-12
    print("  ok")


def _demo_prints():
    print("[DEMO] Uso básico em memória")
    df = pd.DataFrame({"data": ["2024-01", "2024-02", "2024-03"], "tr": [0.0, 0.01, 0.02]})
    tabela = TabelaTR.from_dataframe(df)
    for ym in ["2024-01", "2024-02", "2024-03"]:
        print(f"  TR {ym}: {tabela.taxa_mensal(ym):.6f}")


if __name__ == "__main__":
    print("== Smoke tests TR ==")
    _teste_tabela_from_dataframe()
    _teste_percentual_para_fracao()
    _demo_prints()
    print("Tudo ok.")
