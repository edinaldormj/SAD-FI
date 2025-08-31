from dataclasses import dataclass

@dataclass
class FinanciamentoInput:
    valor_total: float = 300_000.0
    entrada: float = 60_000.0
    prazo_anos: int = 30
    taxa_juros_anual: float = 0.11  # fração

@dataclass
class FontesInput:
    caminho_bancos: str = "dados/bancos.csv"
    caminho_ipca: str = "dados/txjuros/IPCA_BACEN.csv"
    caminho_tr_compat: str = "dados/txjuros/TR_mensal_compat.csv"
