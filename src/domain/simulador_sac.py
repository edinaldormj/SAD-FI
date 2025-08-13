from domain.parcela import Parcela
from domain.simulacao_resultado import SimulacaoResultado
import logging


class SimuladorSAC:
    """
    Simulador de financiamento com amortização constante (SAC) e juros fixos.
    Opcionalmente, aplica TR mensal como indexador do principal (SAC + TR).
    """

    # Tolerância para zerar resíduos numéricos muito pequenos
    _MARGEM_TOLERANCIA = 1e-6

    def __init__(self, financiamento, taxa_juros_anual):
        """
        Inicializa o simulador com os dados do financiamento e a taxa anual fixa.

        Parâmetros:
            financiamento: objeto Financiamento (valor_financiado, prazo_meses, taxa_base_mensal()).
            taxa_juros_anual (float): taxa nominal anual do contrato (ex.: 0.12 para 12% a.a.).
        """
        self.financiamento = financiamento
        self.taxa_juros_anual = taxa_juros_anual

    def simular(self, usar_tr: bool = False, tr_mensal: float | None = None) -> SimulacaoResultado:
        """
        Executa a simulação e retorna um SimulacaoResultado.

        Parâmetros (TR opcional):
            usar_tr (bool): se True, aplica TR mensal na atualização do saldo.
            tr_mensal (float|None): TR mensal em fração decimal (ex.: 0.001 = 0,1% a.m.).
                - MVP: valor constante; no futuro, pode virar provedor/série mensal.

        Regra (SAC + TR):
            saldo_corrigido = saldo_anterior * (1 + TR_mensal) [se usar_tr]
            juros_mes = saldo_corrigido * i_base_mensal
            amortizacao_mes = constante (= principal/prazo), exceto no último mês (ajuste p/ quitar)
            parcela = amortizacao_mes + juros_mes
            saldo_devedor = saldo_corrigido - amortizacao_mes
        """
        lista_parcelas = []

        valor_financiado = self.financiamento.valor_financiado()
        prazo_meses = self.financiamento.prazo_meses
        taxa_base_mensal = self.financiamento.taxa_base_mensal()  # mantém coerência com o domínio
        amortizacao_constante = valor_financiado / prazo_meses
        saldo_devedor = valor_financiado

        # Validação/aviso da TR (quando ativada)
        if usar_tr:
            if tr_mensal is None:
                raise ValueError("usar_tr=True exige tr_mensal definido.")
            if abs(tr_mensal) > 0.01:  # > 1% a.m.
                logging.warning(f"TR mensal fora da faixa usual: {tr_mensal:.6f}")

        for numero_parcela in range(1, prazo_meses + 1):
            # 1) Guarda saldo anterior (antes de qualquer atualização)
            saldo_anterior = saldo_devedor

            # 2) Atualiza o saldo pelo TR (se ativado)
            saldo_corrigido = saldo_anterior * (1 + tr_mensal) if usar_tr else saldo_anterior
            correcao_tr_mes = saldo_corrigido - saldo_anterior  # pode ser 0

            # 3) Juros sobre o saldo corrigido
            juros_mes = saldo_corrigido * taxa_base_mensal

            # 4) Amortização: constante, exceto no último mês (quando TR ativa)
            if usar_tr and numero_parcela == prazo_meses:
                amortizacao_mes = saldo_corrigido  # quitar exatamente o saldo atualizado
            else:
                amortizacao_mes = amortizacao_constante

            # 5) Parcela (amortização + juros)
            valor_parcela = amortizacao_mes + juros_mes

            # 6) Atualiza saldo
            saldo_devedor = saldo_corrigido - amortizacao_mes
            if abs(saldo_devedor) < self._MARGEM_TOLERANCIA:
                saldo_devedor = 0.0

            # 7) Monta a parcela; adiciona atributos extras para exportação/diagnóstico
            parcela = Parcela(
                numero_parcela,
                amortizacao_mes,
                juros_mes,
                valor_parcela,
                saldo_devedor
            )
            # Atributos extras (não quebram compatibilidade)
            try:
                parcela.saldo_anterior = saldo_anterior
                parcela.correcao_tr_mes = correcao_tr_mes
                parcela.saldo_corrigido = saldo_corrigido
            except Exception:
                # Em ambientes muito restritos, ignore atributos dinâmicos
                pass

            lista_parcelas.append(parcela)

        return SimulacaoResultado(lista_parcelas)
