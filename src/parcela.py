class Parcela:
    def __init__(self, numero, amortizacao, juros, valor_total, saldo_devedor):
        self.numero = numero
        self.amortizacao = amortizacao
        self.juros = juros
        self.valor_total = valor_total
        self.saldo_devedor = saldo_devedor

    def __repr__(self):
        return (
            f"Parcela(numero={self.numero}, amortizacao={self.amortizacao:.2f}, "
            f"juros={self.juros:.2f}, valor_total={self.valor_total:.2f}, "
            f"saldo_devedor={self.saldo_devedor:.2f})"
        )

    def __eq__(self, other):
        if not isinstance(other, Parcela):
            return NotImplemented
        return (
            self.numero == other.numero and
            abs(self.amortizacao - other.amortizacao) < 1e-6 and
            abs(self.juros - other.juros) < 1e-6 and
            abs(self.valor_total - other.valor_total) < 1e-6 and
            abs(self.saldo_devedor - other.saldo_devedor) < 1e-6
        )
