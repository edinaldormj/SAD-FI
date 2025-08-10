import pandas as pd

class SimulacaoResultado:
    """
    Representa o resultado de uma simulação de financiamento.

    Armazena a lista de parcelas geradas, o valor total pago ao longo do tempo
    e o total de juros pagos.
    """

    def __init__(self, parcelas: list):
        """
        Inicializa o resultado com a lista de parcelas.

        Parâmetros:
        parcelas (List[Parcela]): Lista de objetos Parcela simulados.
        """
        self.parcelas = parcelas
        self.total_pago = sum(p.valor_total for p in parcelas)
        self.total_juros = sum(p.juros for p in parcelas)

    def __repr__(self):
        """
        Representação resumida do resultado, útil para debug e logs.
        """
        return (
            f"SimulacaoResultado("
            f"parcelas={len(self.parcelas)}, "
            f"total_pago={self.total_pago:.2f}, "
            f"total_juros={self.total_juros:.2f})"
        )

    def to_dict_resumo(self):
        """
        Retorna um dicionário com o resumo numérico da simulação.

        Retorno:
        dict: {'parcelas': int, 'total_pago': float, 'total_juros': float}
        """
        return {
            "parcelas": len(self.parcelas),
            "total_pago": self.total_pago,
            "total_juros": self.total_juros
        }

    def to_dataframe(self):
        """
        Converte o cronograma de parcelas em um DataFrame do Pandas.

        Retorno:
        pandas.DataFrame com colunas:
            n_parcela, data, valor_parcela, amortizacao, juros, saldo_devedor
        """
        dados = []
        for p in self.parcelas:
            dados.append({
                "n_parcela": getattr(p, "numero", None),
                "data": getattr(p, "data", None),
                "valor_parcela": getattr(p, "valor_total", None),
                "amortizacao": getattr(p, "amortizacao", None),
                "juros": getattr(p, "juros", None),
                "saldo_devedor": getattr(p, "saldo_devedor", None)
            })

        df = pd.DataFrame(dados)

        # Ordena por número da parcela se disponível
        if "n_parcela" in df.columns and df["n_parcela"].notna().all():
            df = df.sort_values("n_parcela").reset_index(drop=True)

        return df
