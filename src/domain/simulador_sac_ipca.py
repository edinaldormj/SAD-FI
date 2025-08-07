from domain.parcela import Parcela
from domain.simulacao_resultado import SimulacaoResultado

class SimuladorSAC_IPCA:
    """
    Simulador com amortização constante (SAC) e juros variáveis indexados ao IPCA.
    """

    def __init__(self, financiamento, tabela_ipca):
        """
        Inicializa com os dados do financiamento e a tabela de IPCA mensal.
        """
        self.financiamento = financiamento
        self.tabela_ipca = tabela_ipca

    def simular(self):
        """
        Executa a simulação com juros variáveis pelo IPCA.

        Retorno:
        SimulacaoResultado: Contendo parcelas, total pago e total de juros.
        """
        parcelas = []

        valor = self.financiamento.valor_financiado()
        prazo = self.financiamento.prazo_meses
        amortizacao = valor / prazo
        saldo_devedor = valor

        for numero in range(1, prazo + 1):
            ipca_mensal = self.tabela_ipca.get_ipca(numero)
            juros = saldo_devedor * ipca_mensal
            valor_total = amortizacao + juros

            parcela = Parcela(numero, amortizacao, juros, valor_total, saldo_devedor)
            parcelas.append(parcela)

            saldo_devedor -= amortizacao

        return SimulacaoResultado(parcelas)

