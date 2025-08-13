import os
from domain.financiamento import Financiamento
from domain.simulador_sac import SimuladorSAC
from domain.simulador_sac_ipca import SimuladorSAC_IPCA
from domain.comparador import ComparadorModalidades
from infrastructure.data.tabela_ipca import TabelaIPCA
from domain.recomendador import RecomendadorModalidade
from infrastructure.data.exportador_csv import exportar_cronograma_csv
from typing import Any

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
            sistema=dados_entrada["sistema"],
            taxa_juros_anual=dados_entrada["taxa_juros_anual"],
        )

        if dados_entrada["sistema"] == "SAC":
            simulador = SimuladorSAC(
                financiamento,
                dados_entrada["taxa_juros_anual"]
            )
            # Parâmetros opcionais para TR (MVP como constante mensal)
            usar_tr = bool(dados_entrada.get("usar_tr", False))
            tr_mensal = dados_entrada.get("tr_mensal", None)
            return simulador.simular(usar_tr=usar_tr, tr_mensal=tr_mensal)

        elif dados_entrada["sistema"] == "SAC_IPCA":
            # 📌 Garante que o caminho para o CSV do IPCA seja absoluto
            caminho_ipca = os.path.abspath(dados_entrada["caminho_ipca"])

            # 🔍 Verifica se o arquivo existe antes de prosseguir
            if not os.path.exists(caminho_ipca):
                raise FileNotFoundError(f"Arquivo do IPCA não encontrado: {caminho_ipca}")

            # 📥 Carrega a tabela IPCA a partir do caminho informado
            tabela_ipca = TabelaIPCA(caminho_ipca)

            # ▶️ Cria o simulador SAC+IPCA usando o financiamento e a tabela de índices
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

    def exportar_resultado(self, simulacao_resultado: Any, nome_base: str) -> str:
        """
        Exporta o resultado de uma simulação para CSV.

        Parâmetros:
            simulacao_resultado: objeto que deve possuir o método to_dataframe().
            nome_base (str): Nome base do arquivo (sem extensão).

        Retorno:
            str: Caminho completo do arquivo CSV gerado.
        """
        if not hasattr(simulacao_resultado, "to_dataframe"):
            raise TypeError("O objeto informado não possui o método to_dataframe().")

        df = simulacao_resultado.to_dataframe()

        if getattr(df, "empty", True):
            raise ValueError("O DataFrame está vazio. Nada a exportar.")

        caminho = exportar_cronograma_csv(df, nome_base)
        print(f"✅ Arquivo CSV exportado para: {caminho}")
        return caminho

