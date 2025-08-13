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
        """
        return {
            "parcelas": len(self.parcelas),
            "total_pago": self.total_pago,
            "total_juros": self.total_juros
        }

    # 🔽 NOVO: DataFrame pronto p/ exportação, incluindo colunas TR quando existirem
    def to_dataframe(self):
        """
        Converte o cronograma em um pandas.DataFrame.
        Inclui colunas extras relacionadas à TR (saldo_anterior, correcao_tr_mes, saldo_corrigido)
        caso estes atributos estejam presentes nas parcelas.

        Colunas base:
          n_parcela; amortizacao; juros; valor_parcela; saldo_devedor

        Colunas extras (opcionais):
          saldo_anterior; correcao_tr_mes; saldo_corrigido
        """
        try:
            import pandas as pd
        except Exception as e:
            raise RuntimeError("Pandas é necessário para to_dataframe().") from e

        if not self.parcelas:
            return pd.DataFrame()

        # Detecta se há atributos extras (caso de TR ou indexadores semelhantes)
        tem_saldo_anterior = any(hasattr(p, "saldo_anterior") for p in self.parcelas)
        tem_correcao_tr = any(hasattr(p, "correcao_tr_mes") for p in self.parcelas)
        tem_saldo_corrigido = any(hasattr(p, "saldo_corrigido") for p in self.parcelas)

        linhas = []
        for p in self.parcelas:
            item = {
                "n_parcela": p.numero,
                "amortizacao": p.amortizacao,
                "juros": p.juros,
                "valor_parcela": p.valor_total,
                "saldo_devedor": p.saldo_devedor,
            }
            if tem_saldo_anterior:
                item["saldo_anterior"] = getattr(p, "saldo_anterior", None)
            if tem_correcao_tr:
                item["correcao_tr_mes"] = getattr(p, "correcao_tr_mes", None)
            if tem_saldo_corrigido:
                item["saldo_corrigido"] = getattr(p, "saldo_corrigido", None)
            linhas.append(item)

        # Ordena colunas para legibilidade
        colunas = ["n_parcela"]
        if tem_saldo_anterior:
            colunas += ["saldo_anterior"]
        if tem_correcao_tr:
            colunas += ["correcao_tr_mes"]
        if tem_saldo_corrigido:
            colunas += ["saldo_corrigido"]
        colunas += ["amortizacao", "juros", "valor_parcela", "saldo_devedor"]

        df = pd.DataFrame(linhas, columns=colunas)
        return df

    # 🔽 NOVO: resumo com correção do principal exposta
    def resumo_financeiro(self) -> dict:
        """
        Retorna um dicionário com métricas de transparência:
         - valor_financiado: saldo da primeira parcela antes do pagamento
         - soma_amortizacoes
         - correcao_tr_acumulada = soma_amortizacoes - valor_financiado
         - total_juros
         - total_pago
        """
        if not self.parcelas:
            return {
                "valor_financiado": 0.0,
                "soma_amortizacoes": 0.0,
                "correcao_tr_acumulada": 0.0,
                "total_juros": 0.0,
                "total_pago": 0.0,
            }

        valor_financiado = getattr(self.parcelas[0], "saldo_anterior", None)
        if valor_financiado is None:
            # fallback: nos simuladores atuais, saldo_devedor da 1ª parcela é o saldo anterior
            valor_financiado = self.parcelas[0].saldo_devedor

        soma_amortizacoes = sum(p.amortizacao for p in self.parcelas)
        correcao_tr_acumulada = soma_amortizacoes - valor_financiado

        return {
            "valor_financiado": float(valor_financiado),
            "soma_amortizacoes": float(soma_amortizacoes),
            "correcao_tr_acumulada": float(correcao_tr_acumulada),
            "total_juros": float(self.total_juros),
            "total_pago": float(self.total_pago),
        }
