import pandas as pd

class TabelaIPCA:
    """
    Responsável por carregar e fornecer os valores mensais do IPCA
    a partir de um arquivo CSV.

    Utilizada pelos simuladores para calcular os juros variáveis
    indexados à inflação.
    """

    def __init__(self, caminho_csv: str):
        """
        Inicializa a tabela IPCA lendo os dados de um arquivo CSV.

        Parâmetros:
        caminho_csv (str): Caminho para o arquivo contendo a série histórica do IPCA.
        """
        self.caminho_csv = caminho_csv
        # self.tabela = pd.read_csv(caminho_csv)  # será implementado depois

    def get_ipca(self, mes: int) -> float:
        """
        Retorna o valor percentual do IPCA referente ao mês do financiamento.

        Parâmetros:
        mes (int): Número do mês (1 para o primeiro, 2 para o segundo, etc.)

        Retorno:
        float: Valor do IPCA em formato decimal (ex: 0.0042 para 0,42%)
        """
        pass
