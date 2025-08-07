from domain.parcela import Parcela
from domain.simulacao_resultado import SimulacaoResultado

class SimuladorSAC:
    """
    Simulador de financiamento com amortização constante (SAC),
    com taxa de juros fixa.
    """

    def __init__(self, financiamento, taxa_juros_anual):
        """
        Inicializa o simulador com os dados do financiamento e a taxa anual fixa.
        """
        self.financiamento = financiamento
        self.taxa_juros_anual = taxa_juros_anual

    def simular(self):
        """
        Executa a simulação e retorna um SimulacaoResultado.

        Retorno:
        SimulacaoResultado: Contendo parcelas, total pago e total de juros.
        """
        parcelas = []

        valor = self.financiamento.valor_financiado()
        prazo = self.financiamento.prazo_meses
        taxa_mensal = (1 + self.taxa_juros_anual) ** (1/12) - 1
        amortizacao = valor / prazo
        saldo_devedor = valor

        for numero in range(1, prazo + 1):
            juros = saldo_devedor * taxa_mensal
            valor_total = amortizacao + juros

            parcela = Parcela(numero, amortizacao, juros, valor_total, saldo_devedor)
            parcelas.append(parcela)

            saldo_devedor -= amortizacao

        return SimulacaoResultado(parcelas)

