class Financiamento:
    """
    Representa um contrato de financiamento, contendo informações básicas como
    valor total do bem, valor de entrada, prazo em anos e sistema de amortização.

    A classe também fornece o valor efetivamente financiado e o prazo em meses.
    """

    def __init__(self, valor_total, entrada, prazo_anos, sistema):
        """
        Inicializa um novo financiamento.

        Parâmetros:
        valor_total (float): Valor total do bem a ser financiado.
        entrada (float): Valor pago de entrada, que será subtraído do valor total.
        prazo_anos (int): Duração do financiamento em anos.
        sistema (str): Nome do sistema de amortização utilizado ('SAC', 'PRICE', etc.).
        """
        self.valor_total = valor_total
        self.entrada = entrada
        self.prazo_anos = prazo_anos
        self.sistema = sistema

        # Converte o prazo de anos para meses (com base em 12 meses por ano)
        self.prazo_meses = prazo_anos * 12

    def valor_financiado(self):
        """
        Retorna o valor efetivamente financiado, ou seja,
        o valor total do bem subtraído da entrada.

        Retorno:
        float: Valor a ser financiado.
        """
        return self.valor_total - self.entrada

