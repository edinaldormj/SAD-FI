from dominio.parcela import Parcela

class SimuladorSAC_IPCA:
    """
    Simulador de financiamento com amortização constante (SAC),
    mas com variação nos juros mensais conforme índice IPCA.
    """

    def __init__(self, financiamento, tabela_ipca):
        """
        Inicializa o simulador com os dados do financiamento e a tabela IPCA.

        Parâmetros:
        financiamento (Financiamento): Objeto com valor, entrada, prazo etc.
        tabela_ipca (TabelaIPCA): Objeto com os valores mensais do IPCA.
        """
        self.financiamento = financiamento
        self.tabela_ipca = tabela_ipca

    def simular(self):
        """
        Executa a simulação SAC com juros variáveis conforme IPCA.

        Retorno:
        SimulacaoResultado: Objeto contendo as parcelas simuladas e totais.
        """
        pass  # A lógica da simulação será implementada depois
