from domain.parcela import Parcela
from domain.simulacao_resultado import SimulacaoResultado
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class SimuladorSAC:
    """
    Simulador de financiamento com amortização constante (SAC) e juros fixos.
    Opcionalmente, aplica TR mensal como indexador do principal (SAC + TR).

    Regras adotadas:
      • Sem TR (SAC “puro”): amortização nominal constante = valor_financiado / prazo_meses.
      • Com TR (SAC + TR): amortização “real” constante e corrigida mês a mês pelo fator acumulado
        da TR. Isso implica:
          amort_real_const = valor_financiado / n
          fator_acumulado_1 = (1 + tr_1)
          fator_acumulado_2 = (1 + tr_1) * (1 + tr_2)
          ...
          amortizacao_t = amort_real_const * fator_acumulado_t
        Dessa forma, a soma das amortizações é maior que o valor financiado quando a TR for positiva,
        evidenciando a correção monetária (transparência).
      • Juros incidem sobre o saldo corrigido do mês (antes da amortização).
      • No último mês, a amortização é ajustada para quitar exatamente o saldo corrigido remanescente.
    """

    # Tolerância para zerar resíduos numéricos muito pequenos
    _MARGEM_TOLERANCIA = 1e-6

    def __init__(self, financiamento, taxa_juros_anual: float):
        """
        Parâmetros:
            financiamento: objeto Financiamento (valor_financiado(), prazo_anos, taxa_base_mensal()).
            taxa_juros_anual (float): taxa nominal anual (ex.: 0.12 para 12% a.a.).
        """
        self.financiamento = financiamento
        self.taxa_juros_anual = float(taxa_juros_anual)

    def _taxa_mensal(self) -> float:
        # Usa a conversão efetiva mensal: (1 + i_a)^(1/12) - 1
        return (1.0 + self.taxa_juros_anual) ** (1.0 / 12.0) - 1.0

    def _prazo_meses(self) -> int:
        # Financiamento expõe prazo_anos; admite frações múltiplas de 1/12.
        n = int(round(self.financiamento.prazo_anos * 12))
        if n <= 0:
            raise ValueError("prazo_meses inválido")
        return n

    def simular(
        self,
        usar_tr: bool = False,
        tr_mensal: Optional[float] = None,
        tr_series: Optional[List[float]] = None,
    ) -> SimulacaoResultado:
        """
        Executa a simulação e retorna um SimulacaoResultado.

        Parâmetros (TR opcional):
            usar_tr: ativa correção mensal do saldo por TR.
            tr_mensal: TR constante (fração, ex.: 0.001 para 0,1% ao mês); mantido por compatibilidade.
            tr_series: série de TR (fração) aplicada mês a mês; se faltar valores, replica o último.
                       Tem precedência sobre `tr_mensal` se fornecida.
        """
        valor_financiado = float(self.financiamento.valor_financiado())
        prazo_meses = self._prazo_meses()
        taxa_mensal = self._taxa_mensal()

        # Amortização “real” constante (base) — usada tanto no SAC puro (fator = 1)
        # quanto no SAC+TR (aplicando fator acumulado).
        amort_real_const = valor_financiado / prazo_meses

        # Série TR preparada
        serie = list(tr_series or [])
        tem_serie = len(serie) > 0
        tr_const = float(tr_mensal or 0.0)

        # Estado
        saldo_devedor = valor_financiado
        fator_acumulado = 1.0
        lista_parcelas: List[Parcela] = []

        for k in range(1, prazo_meses + 1):
            # 1) Saldo antes de correções/juros (transparência)
            saldo_anterior = saldo_devedor

            # 2) TR do mês
            if usar_tr:
                if tem_serie:
                    idx = min(k - 1, len(serie) - 1)
                    tr_mes = float(serie[idx])
                else:
                    tr_mes = tr_const
            else:
                tr_mes = 0.0

            # 3) Corrige saldo do mês pela TR
            saldo_corrigido = saldo_anterior * (1.0 + tr_mes)

            # 4) Atualiza fator acumulado da TR (para amortização “real” constante corrigida)
            fator_acumulado *= (1.0 + tr_mes)

            # 5) Amortização do mês
            if k < prazo_meses:
                # SAC puro: amortização = amort_real_const * 1.0 (fator acumulado = 1)
                # SAC+TR: amortização corrigida pelo fator acumulado
                amortizacao_mes = amort_real_const * fator_acumulado
                # Em casos extremos (TR muito alta), garante limite superior
                if amortizacao_mes > saldo_corrigido:
                    amortizacao_mes = saldo_corrigido
            else:
                # Último mês: quita tudo que restou do principal corrigido
                amortizacao_mes = saldo_corrigido

            # 6) Juros do mês sobre saldo corrigido
            juros_mes = saldo_corrigido * taxa_mensal

            # 7) Valor total da parcela e novo saldo
            valor_parcela = amortizacao_mes + juros_mes
            saldo_devedor = saldo_corrigido - amortizacao_mes

            # 8) Saneamento numérico
            if abs(saldo_devedor) < self._MARGEM_TOLERANCIA:
                saldo_devedor = 0.0

            # 9) Cria parcela
            parcela = Parcela(
                numero=k,
                amortizacao=amortizacao_mes,
                juros=juros_mes,
                valor_total=valor_parcela,
                saldo_devedor=saldo_devedor,
            )

            # 10) Atributos de transparência (não quebram compatibilidade)
            try:
                parcela.saldo_anterior = saldo_anterior
                parcela.correcao_tr_mes = tr_mes
                parcela.saldo_corrigido = saldo_corrigido
            except Exception:
                pass  # ambientes restritos: ignore atributos dinâmicos

            lista_parcelas.append(parcela)

        return SimulacaoResultado(lista_parcelas)
