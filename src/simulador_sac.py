from parcela import Parcela

class SimuladorSAC:
    """
    Classe responsável por gerar o cronograma de parcelas de um financiamento
    utilizando o sistema de amortização constante (SAC).
    """

    def __init__(self, financiamento, taxa_juros_anual):
        """
        Inicializa o simulador com um objeto Financiamento e a taxa de juros.

        Parâmetros:
        financiamento (Financiamento): Objeto com valor total, entrada, prazo e sistema.
        taxa_juros_anual (float): Taxa de juros anual em formato decimal (ex: 0.10 para 10%).
        """
        self.financiamento = financiamento
        self.taxa_juros_anual = taxa_juros_anual

    def simular(self):
        """
        Executa a simulação SAC e retorna uma lista de objetos Parcela.

        Retorno:
        List[Parcela]: Lista com o detalhamento de cada parcela do financiamento.
        """
        parcelas = []

        valor = self.financiamento.valor_financiado()  # valor a financiar após entrada
        prazo = self.financiamento.prazo_meses         # prazo já convertido pela classe
        taxa_juros_mensal = (1 + self.taxa_juros_anual) ** (1/12) - 1
        amortizacao = valor / prazo
        saldo_devedor = valor

        for numero in range(1, prazo + 1):
            juros = saldo_devedor * taxa_juros_mensal
            valor_total = amortizacao + juros

            parcela = Parcela(
                numero=numero,
                amortizacao=amortizacao,
                juros=juros,
                valor_total=valor_total,
                saldo_devedor=saldo_devedor
            )
            parcelas.append(parcela)
            saldo_devedor -= amortizacao

        return parcelas
