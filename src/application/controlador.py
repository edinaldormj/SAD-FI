from domain.financiamento import Financiamento
from domain.simulador_sac import SimuladorSAC
from domain.simulador_sac_ipca import SimuladorSAC_IPCA
from domain.comparador import ComparadorModalidades
from infrastructure.data.tabela_ipca import TabelaIPCA
from domain.recomendador import RecomendadorModalidade

class ControladorApp:
    """
    Controlador principal da aplicação. Orquestra a execução das simulações,
    comparações e exportações com base nos dados fornecidos pelo usuário.
    """

    def __init__(self):
        """
        Inicializa o controlador com os componentes necessários.
        """
        self.comparador = None  # será usado mais tarde

    def executar_simulacao(self, dados_entrada: dict):
        """
        Executa a simulação a partir dos dados fornecidos pelo usuário.

        Parâmetros:
        dados_entrada (dict): Parâmetros do financiamento. Deve conter:
            - valor_total (float)
            - entrada (float)
            - prazo_anos (int)
            - sistema (str): "SAC" ou "SAC_IPCA"
            - taxa_juros_anual (float): se sistema == "SAC"
            - caminho_ipca (str): se sistema == "SAC_IPCA"

        Retorno:
        SimulacaoResultado
        """
        financiamento = Financiamento(
            valor_total=dados_entrada["valor_total"],
            entrada=dados_entrada["entrada"],
            prazo_anos=dados_entrada["prazo_anos"],
            sistema=dados_entrada["sistema"]
        )

        if dados_entrada["sistema"] == "SAC":
            simulador = SimuladorSAC(
                financiamento,
                dados_entrada["taxa_juros_anual"]
            )
        elif dados_entrada["sistema"] == "SAC_IPCA":
            tabela_ipca = TabelaIPCA(dados_entrada["caminho_ipca"])
            simulador = SimuladorSAC_IPCA(financiamento, tabela_ipca)
        else:
            raise ValueError("Sistema de amortização não suportado.")

        return simulador.simular()




    def comparar_modalidades(self, resultado1, resultado2) -> str:
        """
        Compara dois resultados de simulação usando a lógica de negócio.

        Parâmetros:
        - resultado1: SimulacaoResultado da modalidade 1
        - resultado2: SimulacaoResultado da modalidade 2

        Retorno:
        - str: Texto com interpretação da vantagem de uma modalidade
        """
        if not self.comparador:
            self.comparador = ComparadorModalidades()

        return self.comparador.comparar(resultado1, resultado2)


    def obter_recomendacao(self, mensagem_comparacao: str) -> str:
        """
        Gera uma recomendação com base na mensagem retornada pela função de comparação.

        Parâmetros:
        - mensagem_comparacao (str): Texto retornado por `comparar_modalidades()`

        Retorno:
        - str: Exemplo -> "💡 Recomendado: SAC IPCA+"
        """
        recomendador = RecomendadorModalidade()
        dados = {"mensagem_comparacao": mensagem_comparacao}
        return recomendador.recomendar(dados)
        