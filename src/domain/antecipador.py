class AntecipadorParcelas:
    """
    Classe responsável por simular a antecipação de parcelas ou amortização extraordinária
    em financiamentos imobiliários.

    Essa lógica é aplicada sobre um conjunto de parcelas já simuladas.
    """

    def __init__(self, parcelas):
        """
        Inicializa o antecipador com a lista de parcelas originais.

        Parâmetros:
        parcelas (List[Parcela]): Lista de parcelas do financiamento.
        """
        self.parcelas = parcelas

    def antecipar(self, quantidade: int):
        """
        Simula a quitação antecipada de um número de parcelas.

        Parâmetros:
        quantidade (int): Número de parcelas a antecipar.

        Retorno:
        List[Parcela]: Nova lista de parcelas com ajustes.
        """
        pass
