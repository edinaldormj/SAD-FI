from __future__ import annotations

import os
import sys
import logging                               # ALTERAÇÃO: usar logging em vez de print
from typing import Any, Optional             # ALTERAÇÃO: tipagens úteis
from typing import Dict, List, Tuple, Optional


from domain.financiamento import Financiamento
from domain.simulador_sac import SimuladorSAC
from domain.simulador_sac_ipca import SimuladorSAC_IPCA
from domain.comparador import ComparadorModalidades
from infrastructure.data.tabela_ipca import TabelaIPCA
from infrastructure.data.leitor_bancos import carregar_bancos_csv #NOVO Sprint 3
# from infrastructure.data.coletor_bacen import coletar_ipca_433  # novo (quando integrar)
# from infrastructure.data.coletor_bacen import obter_ipca_df, df_para_tabela_ipca # novo (quando integrar)
from application.comparador import comparar_varios, recomendar # novo
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
    

    def _carregar_tabela_ipca(self, fonte_ipca: dict | None, exige_ipca: bool):
        """
        Helper interno para resolver e carregar a fonte do IPCA.

        Parâmetros:
        fonte_ipca: dict | None
            - CSV local: {"caminho_ipca": "dados/ipca.csv"}
            - BACEN 433: {"usar_bacen": True, "meses": 24}  (pendente até existir TabelaIPCA.from_dataframe)
        exige_ipca: bool
            True se há pelo menos um banco SAC_IPCA a ser simulado. Evita
            carregar IPCA quando todos os bancos são SAC fixo.

        Retorno:
        TabelaIPCA | None
            Instância pronta quando necessário; None quando não exigido.

        Erros:
        KeyError, ValueError: quando a fonte é obrigatória/ inválida.
        FileNotFoundError: quando caminho_csv não existe (propagado do construtor).
        NotImplementedError: caminho BACEN ainda não integrado (até existir from_dataframe).
        """
        # Se nenhum banco exige IPCA, não há o que carregar
        if not exige_ipca:
            logger.info("Nenhum banco SAC_IPCA na lista. IPCA não será carregado.")
            return None

        # Fonte do IPCA é obrigatória se existe SAC_IPCA
        if not fonte_ipca:
            raise KeyError(
                "Fonte do IPCA não informada para bancos SAC_IPCA. "
                "Use {'caminho_ipca': '...'} (CSV) ou {'usar_bacen': True, 'meses': N} (BACEN)."
            )

        # CSV local: mantém o contrato atual (TabelaIPCA lê CSV tratado e armazena %; get_ipca retorna fração)
        if "caminho_ipca" in fonte_ipca:
            caminho = str(fonte_ipca["caminho_ipca"]).strip()
            logger.info("IPCA: carregando a partir de CSV local: %s", caminho)
            tabela = TabelaIPCA(caminho)
            return tabela

        # BACEN (série 433): integração será habilitada após adicionar TabelaIPCA.from_dataframe(df)
        if fonte_ipca.get("usar_bacen"):
            meses = int(fonte_ipca.get("meses", 24))
            logger.info("IPCA: solicitação de BACEN 433 por %d meses (aguardando from_dataframe).", meses)
            # Exemplo do fluxo futuro (comentado até existir from_dataframe e o coletor):
            # from infrastructure.data.coletor_bacen import coletar_ipca_433
            # df = coletar_ipca_433(meses=meses)         # df com colunas ['data','ipca'], em % (ou fração)
            # tabela = TabelaIPCA.from_dataframe(df)     # Opção A: armazenar em %, entregar fração
            # return tabela
            raise NotImplementedError(
                "Coleta BACEN 433 pendente de TabelaIPCA.from_dataframe(df). "
                "Use CSV local por enquanto: {'caminho_ipca': 'dados/ipca.csv'}."
            )
        
        # Caso a chave não seja reconhecida
        raise ValueError(
            "Fonte do IPCA inválida. Informe 'caminho_ipca' (CSV) ou 'usar_bacen' (bool)."
        )


    def simular_multiplos_bancos(
        self,
        caminho_bancos_csv: str,
        dados_financiamento: dict,
        fonte_ipca: dict | None = None,
    ):
        """
        Executa simulação em lote para múltiplos bancos, produz ranking e recomendação.
        (docstring mantida como antes)
        """
        # ---------------------- 1) Carregar bancos ---------------------- #
        bancos = carregar_bancos_csv(caminho_bancos_csv)
        if not bancos:
            raise ValueError("Nenhum banco encontrado em bancos.csv.")

        logger.info("Bancos carregados: %d entradas a simular.", len(bancos))

        # ---------------- 2) Resolver IPCA (uma única vez) --------------- #
        exige_ipca = any((str(b.get("sistema", "")).upper() == "SAC_IPCA") for b in bancos)
        tabela_ipca = self._carregar_tabela_ipca(fonte_ipca, exige_ipca)

        # ------------------ 3) Simular por banco/modalidade --------------- #
        resultados: dict[str, SimulacaoResultado] = {}

        for b in bancos:
            nome_banco = str(b["nome"]).strip()
            sistema = str(b["sistema"]).upper().strip()      # "SAC" ou "SAC_IPCA"
            taxa_anual = float(b["taxa_anual"])

            # Monta Financiamento reusando helpers existentes (validações centralizadas)
            fin = self._montar_financiamento(dados_financiamento, sistema, taxa_anual)

            if sistema == "SAC":
                simulador = SimuladorSAC(fin, taxa_anual)    # override explícito de taxa anual
                resultado = simulador.simular()
                rotulo = f"{nome_banco} – SAC"
            elif sistema == "SAC_IPCA":
                if tabela_ipca is None:
                    # Defesa adicional (não deveria ocorrer se _carregar_tabela_ipca foi chamado com exige_ipca=True)
                    raise RuntimeError("Tabela IPCA não carregada para banco SAC_IPCA.")
                simulador = SimuladorSAC_IPCA(financiamento=fin, tabela_ipca=tabela_ipca)
                resultado = simulador.simular()
                rotulo = f"{nome_banco} – SAC IPCA+"
            else:
                # Defesa contra valores inesperados (o leitor deve normalizar, mas mantém robustez)
                raise ValueError(f"Sistema de amortização inválido em bancos.csv: {sistema!r}")

            resultados[rotulo] = resultado

        # ------------------------ 4) Construir ranking -------------------- #
        # Usamos o comparador centralizado (mantém lógica de ordenação e estabilidade)
        try:
            ranking = comparar_varios(resultados)  # retorna List[Tuple[rotulo, total_pago]]
        except Exception as e:
            # Em caso de erro ao extrair total_pago, deixamos claro qual resultado é problemático
            raise RuntimeError(f"Erro ao construir ranking: {e}")

        # -------------------- 5) Mensagem de recomendação ---------------- #
        # Montamos um mapeamento simples de modalidades (rótulo -> "SAC" / "SAC IPCA+")
        modalidades = {}
        for rotulo in resultados.keys():
            # regra simples: se 'IPCA' no rótulo assumimos SAC IPCA+, caso contrário SAC
            modalidades[rotulo] = "SAC IPCA+" if "IPCA" in rotulo.upper() else "SAC"

        mensagem = recomendar(ranking, modalidades=modalidades)

        # ----------------------------- Logs ------------------------------ #
        qtd_bancos = len(bancos)
        qtd_sac_ipca = sum(1 for b in bancos if str(b["sistema"]).upper() == "SAC_IPCA")
        vencedor, menor_total = ranking[0]
        logger.info(
            "Simulação multi-bancos concluída: %d bancos (SAC_IPCA=%d). Vencedor=%s ; total=%.2f",
            qtd_bancos, qtd_sac_ipca, vencedor, menor_total
        )

        return resultados, ranking, mensagem



