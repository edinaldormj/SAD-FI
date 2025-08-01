class Parcela:
    """
    Representa uma única parcela de um financiamento.

    Cada parcela contém:
    - número da parcela
    - valor da amortização (parte que reduz a dívida)
    - valor dos juros
    - valor total da parcela (amortização + juros)
    - saldo devedor antes do pagamento dessa parcela
    """

    def __init__(self, numero, amortizacao, juros, valor_total, saldo_devedor):
        """
        Inicializa uma nova parcela com os valores fornecidos.

        Parâmetros:
        numero (int): Número da parcela (ex: 1, 2, 3...).
        amortizacao (float): Valor da amortização da dívida nessa parcela.
        juros (float): Valor dos juros cobrados nessa parcela.
        valor_total (float): Valor total da parcela (amortização + juros).
        saldo_devedor (float): Valor da dívida antes do pagamento dessa parcela.
        """
        self.numero = numero
        self.amortizacao = amortizacao
        self.juros = juros
        self.valor_total = valor_total
        self.saldo_devedor = saldo_devedor

    def __repr__(self):
        """
        Retorna uma representação textual legível da parcela, útil para debug.

        Exemplo:
        Parcela(numero=1, amortizacao=1000.00, juros=500.00, valor_total=1500.00, saldo_devedor=90000.00)
        """
        return (
            f"Parcela(numero={self.numero}, amortizacao={self.amortizacao:.2f}, "
            f"juros={self.juros:.2f}, valor_total={self.valor_total:.2f}, "
            f"saldo_devedor={self.saldo_devedor:.2f})"
        )

    def __eq__(self, other):
        """
        Compara duas parcelas para saber se são "iguais".

        Retorna True se:
        - os números das parcelas forem iguais
        - e todos os valores numéricos forem praticamente iguais (tolerância de erro pequena)

        Isso é útil para testes automatizados com assert.
        """
        if not isinstance(other, Parcela):
            return NotImplemented

        # Usa comparação com tolerância para evitar erro com ponto flutuante
        return (
            self.numero == other.numero and
            abs(self.amortizacao - other.amortizacao) < 1e-6 and
            abs(self.juros - other.juros) < 1e-6 and
            abs(self.valor_total - other.valor_total) < 1e-6 and
            abs(self.saldo_devedor - other.saldo_devedor) < 1e-6
        )

