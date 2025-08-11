class Financiamento:
    """
    Representa um contrato de financiamento...
    """

    def __init__(self, valor_total, entrada, prazo_anos, sistema, taxa_juros_anual: float | None = None):
        """
        ...
        taxa_juros_anual (float|None): taxa nominal anual do contrato (ex.: 0.12 para 12% a.a.).
        """
        self.valor_total = valor_total
        self.entrada = entrada
        self.prazo_anos = prazo_anos
        self.sistema = sistema
        self.taxa_juros_anual = taxa_juros_anual  # <-- NOVO

        # ✅ meses devem ser inteiros; aceita prazo_anos fracionário em múltiplos de 1/12
        self.prazo_meses = int(round(prazo_anos * 12))
        if abs(self.prazo_meses - prazo_anos * 12) > 1e-9:
            raise ValueError("prazo_anos deve ser múltiplo de 1/12.")

    def valor_financiado(self):
        return self.valor_total - self.entrada

    def taxa_base_mensal(self) -> float:
        """
        Converte a taxa anual para efetiva mensal: (1 + i_a)^(1/12) - 1.
        Exige taxa_juros_anual definida.
        """
        if self.taxa_juros_anual is None:
            raise ValueError("taxa_juros_anual não definida no Financiamento.")
        return (1.0 + self.taxa_juros_anual) ** (1.0 / 12.0) - 1.0

