class Financiamento:
    def __init__(self, valor_total, entrada, prazo_anos, sistema):
        self.valor_total = valor_total
        self.entrada = entrada
        self.prazo_anos = prazo_anos
        self.sistema = sistema
        self.prazo_meses = prazo_anos * 12

    def valor_financiado(self):
        return self.valor_total - self.entrada
