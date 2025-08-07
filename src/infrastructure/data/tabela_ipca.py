from infrastructure.data.leitor_csv import ler_csv

class TabelaIPCA:
    """
    Responsável por carregar e fornecer os valores mensais do IPCA
    a partir de um arquivo CSV já tratado.

    Utilizada pelos simuladores para calcular os juros variáveis indexados à inflação.
    """

    def __init__(self, caminho_csv: str):
        """
        Inicializa a tabela IPCA lendo os dados do arquivo.

        Parâmetros:
        caminho_csv (str): Caminho para o arquivo CSV contendo os dados do IPCA.
        """
        self.tabela = ler_csv(caminho_csv)

    def get_ipca(self, mes: int) -> float:
        """
        Retorna o valor percentual do IPCA correspondente ao mês do financiamento.

        Parâmetros:
        mes (int): Número do mês no financiamento (1 para o primeiro, 2 para o segundo, etc.)

        Retorno:
        float: Valor do IPCA em formato decimal (ex: 0.0042 para 0,42%)

        Exceção:
        IndexError: Se o mês solicitado for inválido.
        """
        if mes < 1 or mes > len(self.tabela):
            raise IndexError(f"Mês {mes} fora do intervalo disponível (1 a {len(self.tabela)})")
        return self.tabela.loc[mes - 1, "ipca"] / 100  # converte de % para decimal