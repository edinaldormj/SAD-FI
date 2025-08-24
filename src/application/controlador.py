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
from infrastructure.data.tabela_tr import TabelaTR
from infrastructure.data.coletor_tr import ColetorTR
from infrastructure.data.leitor_bancos import carregar_bancos_csv #NOVO Sprint 3
# from infrastructure.data.coletor_bacen import coletar_ipca_433  # novo (quando integrar)
from infrastructure.data.coletor_bacen import obter_ipca_df, df_para_tabela_ipca
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
        if sistema not in {"SAC", "SAC_IPCA", "SAC_TR"}:
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

    def _carregar_tabela_tr(self, fonte_tr: dict|None, exige_tr: bool) -> TabelaTR|None:
        if not exige_tr: return None
        if not fonte_tr: raise KeyError("Fonte da TR não informada.")
        if fonte_tr.get("fixture_csv_path"):
            coletor = ColetorTR(fixture_csv_path=fonte_tr["fixture_csv_path"], online=False)
        elif fonte_tr.get("online"):
            coletor = ColetorTR(fixture_csv_path=None, online=True, serie=fonte_tr.get("serie"))
        else:
            raise ValueError("Fonte da TR inválida. Informe 'fixture_csv_path' ou 'online'.")
        df_tr = coletor.coletar(inicio=fonte_tr.get("inicio"), fim=fonte_tr.get("fim"))
        return TabelaTR.from_dataframe(df_tr)

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
    

    def _carregar_tabela_ipca(self, fonte_ipca: dict|None, exige_ipca: bool) -> TabelaIPCA|None:
        if not exige_ipca: return None
        if not fonte_ipca: raise KeyError("Fonte do IPCA não informada.")
        if fonte_ipca.get("usar_bacen"):
            meses = int(fonte_ipca.get("meses", 24))
            df_ipca = obter_ipca_df(meses=meses)
            return TabelaIPCA.from_dataframe(df_ipca)
        if "caminho_ipca" in fonte_ipca:
            return TabelaIPCA(fonte_ipca["caminho_ipca"])
        raise ValueError("Fonte do IPCA inválida.")


    def simular_multiplos_bancos(self, caminho_bancos_csv, dados_financiamento, fonte_ipca=None, fonte_tr=None):
        bancos = carregar_bancos_csv(caminho_bancos_csv)
        if not bancos:
            raise ValueError("Nenhum banco encontrado em bancos.csv.")

        exige_ipca = any(b["sistema"].upper()=="SAC_IPCA" for b in bancos)
        exige_tr   = any(b["sistema"].upper()=="SAC_TR"   for b in bancos)

        # --- IPCA (uma vez) ---
        tabela_ipca = self._carregar_tabela_ipca(fonte_ipca, exige_ipca)

        # acolchoa IPCA se necessário
        if tabela_ipca is not None:
            prazo_meses = int(round(dados_financiamento["prazo_anos"] * 12))
            tam = len(tabela_ipca.tabela)
            if tam < prazo_meses:
                ultimo = float(tabela_ipca.tabela.loc[tam-1, "ipca"])
                faltam = prazo_meses - tam
                import pandas as pd
                pad = pd.DataFrame({"ipca": [ultimo]*faltam})
                tabela_ipca.tabela = pd.concat([tabela_ipca.tabela, pad], ignore_index=True)

        # --- TR (uma vez) ---
        tr_series = None  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< (novo)
        tabela_tr = self._carregar_tabela_tr(fonte_tr, exige_tr)
        if tabela_tr is not None and getattr(tabela_tr, "df", None) is not None and "tr" in tabela_tr.df.columns:
            tr_series = tabela_tr.df["tr"].tolist()

        resultados = {}
        for b in bancos:
            nome = b["nome"].strip()
            sistema = b["sistema"].upper().strip()
            taxa = float(b["taxa_anual"])

            fin = self._montar_financiamento(dados_financiamento, sistema, taxa)

            if sistema == "SAC":
                resultado = SimuladorSAC(fin, taxa).simular()
                rotulo = f"{nome} – SAC"

            elif sistema == "SAC_IPCA":
                if tabela_ipca is None:
                    raise RuntimeError("IPCA não carregado.")
                resultado = SimuladorSAC_IPCA(fin, tabela_ipca).simular()
                rotulo = f"{nome} – SAC IPCA+"

            elif sistema == "SAC_TR":
                # garante que tr_series existe e tem conteúdo
                if tr_series is None or len(tr_series) == 0:
                    raise RuntimeError("TR não carregada (tr_series vazio).")
                resultado = SimuladorSAC(fin, taxa).simular(usar_tr=True, tr_series=tr_series)
                rotulo = f"{nome} – SAC TR"

            else:
                raise ValueError(f"Sistema inválido: {sistema!r}")

            resultados[rotulo] = resultado

        from application.comparador import mapear_modalidades, comparar_varios, recomendar
        ranking = comparar_varios(resultados)
        mensagem = recomendar(ranking, modalidades=mapear_modalidades(list(resultados.keys())))
        return resultados, ranking, mensagem





