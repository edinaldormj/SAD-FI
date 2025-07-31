class SimulacaoResultado:
    def __init__(self, lista_parcelas):
        self.lista_parcelas = lista_parcelas
        self.total_pago = sum(p.valor_total for p in lista_parcelas)
        self.total_juros = sum(p.juros for p in lista_parcelas)
