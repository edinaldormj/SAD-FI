import os
import logging                               # ALTERAÇÃO: usar logging em vez de print
from typing import Any, Optional             # ALTERAÇÃO: tipagens úteis

from domain.financiamento import Financiamento
from domain.simulador_sac import SimuladorSAC
from domain.simulador_sac_ipca import SimuladorSAC_IPCA
from domain.comparador import ComparadorModalidades
from infrastructure.data.tabela_ipca import TabelaIPCA
from domain.recomendador import RecomendadorModalidade
from infrastructure.data.exportador_csv import exportar_cronograma_csv
from domain.simulacao_resultado import SimulacaoResultado   # ALTERAÇÃO: tipagem de retorno

logger = logging.getLogger(__name__)         # ALTERAÇÃO: logger do módulo


class ControladorApp:
    """
    Controlador principal da aplicação. Orquestra a execução das simulações,
    comparações e exportações com base nos dados fornecidos pelo usuário.
    """

    def __init__(self):
        """
        Inicializa o controlador com os componentes necessários.
        """
        self.comparador: Optional[ComparadorModalidades] = None  # ALTERAÇÃO: anotação de tipo

    # ------------------------ Helpers privados ------------------------ #
    def _validar_campos_comuns(self, dados: dict) -> tuple[str, float]:
        """VALIDA sistema e taxa_juros_anual. Retorna (sistema_normalizado, taxa_anual)."""
        sistema = str(dados.get("sistema", "")).upper()          # ALTERAÇÃO: normalização e leitura segura
        if sistema not in {"SAC", "SAC_IPCA"}:
            raise ValueError(f"Sistema de amortização não suportado: {sistema!r}")  # ALTERAÇÃO: erro claro

        taxa_anual = dados.get("taxa_juros_anual")               # ALTERAÇÃO: evitar KeyError
        if taxa_anual is None:
            # IPCA/TR corrigem o saldo; a taxa base anual é obrigatória em ambas
            raise KeyError("taxa_juros_anual ausente: é obrigatória para SAC e SAC_IPCA.")  # ALTERAÇÃO
        return sistema, float(taxa_anual)

    def _validar_ipca(self, dados: dict) -> str:
        """VALIDA e retorna caminho absoluto do arquivo IPCA."""
        caminho_ipca_in = dados.get("caminho_ipca")
        if not caminho_ipca_in:
            raise KeyError("caminho_ipca ausente para o sistema SAC_IPCA.")          # ALTERAÇÃO
        caminho_ipca = os.path.abspath(caminho_ipca_in)                               # ALTERAÇÃO
        if not os.path.exists(caminho_ipca):
            raise FileNotFoundError(f"Arquivo do IPCA não encontrado: {caminho_ipca}")  # ALTERAÇÃO
        return caminho_ipca

    def _montar_financiamento(self, dados: dict, sistema: str, taxa_anual: float) -> Financiamento:
        """Cria o objeto Financiamento com valores validados."""
        return Financiamento(
            valor_total=dados["valor_total"],
            entrada=dados["entrada"],
            prazo_anos=dados["prazo_anos"],
            sistema=sistema,                          # ALTERAÇÃO: usar valor normalizado
            taxa_juros_anual=taxa_anual,              # ALTERAÇÃO: passar taxa validada
        )

    # ------------------------ API pública ------------------------ #
    def executar_simulacao(self, dados_entrada: dict) -> SimulacaoResultado:   # ALTERAÇÃO: tipagem de retorno
        """
        Executa a simulação a partir dos dados fornecidos pelo usuário.

        Parâmetros:
          dados_entrada (dict): Parâmetros do financiamento. Deve conter:
            - valor_total (float)
            - entrada (float)
            - prazo_anos (int)
            - sistema (str): "SAC" ou "SAC_IPCA"
            - taxa_juros_anual (float): obrigatória para ambas as modalidades   # ALTERAÇÃO: explicitação
            - caminho_ipca (str): obrigatório se sistema == "SAC_IPCA"

        Retorno:
          SimulacaoResultado
        """
        # --------- VALIDAÇÕES PRÉVIAS ---------
        sistema, taxa_anual = self._validar_campos_comuns(dados_entrada)      # ALTERAÇÃO: extrai helper

        if sistema == "SAC_IPCA":
            caminho_ipca = self._validar_ipca(dados_entrada)                   # ALTERAÇÃO: extrai helper

        # --------- CONSTRUÇÃO DO FINANCIAMENTO ---------
        financiamento = self._montar_financiamento(dados_entrada, sistema, taxa_anual)  # ALTERAÇÃO: helper

        # --------- ESCOLHA E EXECUÇÃO DA MODALIDADE ---------
        if sistema == "SAC":
            simulador = SimuladorSAC(financiamento, taxa_anual)

            # Parâmetros opcionais para TR (MVP como constante mensal)
            usar_tr = bool(dados_entrada.get("usar_tr", False))
            tr_mensal = dados_entrada.get("tr_mensal", None)

            # Validação adicional da TR (opcional)
            if usar_tr:
                if tr_mensal is not None:
                    if not isinstance(tr_mensal, (int, float)):
                        raise TypeError(f"tr_mensal inválido: {tr_mensal!r}. Deve ser numérico.")  # ALTERAÇÃO
                    if tr_mensal < 0:
                        raise ValueError(f"tr_mensal inválido: {tr_mensal}. Não pode ser negativo.")  # ALTERAÇÃO
                else:
                    logger.warning(  # ALTERAÇÃO: logging no lugar de print
                        "Nenhum valor para tr_mensal fornecido com usar_tr=True. "
                        "Usando cálculo ou padrão do simulador."
                    )

            return simulador.simular(usar_tr=usar_tr, tr_mensal=tr_mensal)

        # SAC_IPCA
        tabela_ipca = TabelaIPCA(caminho_ipca)          # ALTERAÇÃO: caminho já validado
        simulador = SimuladorSAC_IPCA(financiamento, tabela_ipca)
        return simulador.simular()

    def comparar_modalidades(self, resultado1: SimulacaoResultado,
                             resultado2: SimulacaoResultado) -> str:           # ALTERAÇÃO: tipagem de args
        """
        Compara dois resultados de simulação usando a lógica de negócio.
        """
        if self.comparador is None:                     # ALTERAÇÃO: checagem explícita
            self.comparador = ComparadorModalidades()
        return self.comparador.comparar(resultado1, resultado2)

    def obter_recomendacao(self, mensagem_comparacao: str) -> str:
        """
        Gera uma recomendação com base na mensagem retornada pela função de comparação.
        """
        recomendador = RecomendadorModalidade()
        dados = {"mensagem_comparacao": mensagem_comparacao}
        return recomendador.recomendar(dados)

    def exportar_resultado(self, simulacao_resultado: Any, nome_base: str) -> str:
        """
        Exporta o resultado de uma simulação para CSV.
        """
        if not hasattr(simulacao_resultado, "to_dataframe"):
            raise TypeError("O objeto informado não possui o método to_dataframe().")

        df = simulacao_resultado.to_dataframe()

        if getattr(df, "empty", True):
            raise ValueError("O DataFrame está vazio. Nada a exportar.")

        caminho = exportar_cronograma_csv(df, nome_base)
        logger.info("Arquivo CSV exportado para: %s", caminho)   # ALTERAÇÃO: logging no lugar de print
        return caminho
