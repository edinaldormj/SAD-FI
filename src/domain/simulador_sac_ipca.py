from domain.parcela import Parcela
from domain.simulacao_resultado import SimulacaoResultado


class SimuladorSAC_IPCA:
    """
    Simulador com amortização constante (SAC) e juros variáveis indexados ao IPCA.

    Regra revisada:
    - O saldo devedor é corrigido mensalmente pelo IPCA (positivo ou negativo).
    - Após a correção, aplica-se a taxa de juros base sobre o saldo corrigido.
    - A amortização é constante ao longo do prazo, exceto no último mês, quando
      é ajustada para quitar exatamente o saldo final corrigido.
    - O saldo final deve ser próximo de zero, corrigindo pequenos resíduos numéricos.
    """

    # Margem de tolerância para evitar saldo residual por arredondamento
    _MARGEM_TOLERANCIA = 1e-6

    def __init__(self, financiamento, tabela_ipca):
        """
        Inicializa com os dados do financiamento e a tabela de IPCA mensal.

        Parâmetros:
        financiamento: objeto Financiamento, contendo:
            - valor_financiado()
            - prazo_meses
            - taxa_base_mensal()
        tabela_ipca: objeto com método get_ipca(numero_mes) retornando variação mensal (fração decimal).
        """
        self.financiamento = financiamento
        self.tabela_ipca = tabela_ipca

    def simular(self):
        """
        Executa a simulação do financiamento SAC + IPCA.

        Retorno:
        SimulacaoResultado: Contendo lista de parcelas, total pago e total de juros.
        """
        lista_parcelas = []

        valor_financiado = self.financiamento.valor_financiado()
        prazo_meses = self.financiamento.prazo_meses
        taxa_juros_base_mensal = self.financiamento.taxa_base_mensal()

        amortizacao_constante = valor_financiado / prazo_meses
        saldo_devedor = valor_financiado

        for numero_parcela in range(1, prazo_meses + 1):
            # 1. Corrige o saldo devedor pelo IPCA do mês (pode ser negativo)
            ipca_mensal = self.tabela_ipca.get_ipca(numero_parcela)
            saldo_devedor_corrigido = saldo_devedor * (1 + ipca_mensal)

            # 2. Calcula os juros do mês sobre o saldo corrigido
            juros_mes = saldo_devedor_corrigido * taxa_juros_base_mensal

            # 3. Ajusta a amortização no último mês para quitar o saldo final
            if numero_parcela == prazo_meses:
                amortizacao_mes = saldo_devedor_corrigido
            else:
                amortizacao_mes = amortizacao_constante

            # 4. Calcula o valor total da parcela
            valor_parcela = amortizacao_mes + juros_mes

            # 5. Atualiza o saldo devedor para o próximo mês
            saldo_devedor = saldo_devedor_corrigido - amortizacao_mes

            # 6. Corrige saldo final residual por erro numérico
            if abs(saldo_devedor) < self._MARGEM_TOLERANCIA:
                saldo_devedor = 0.0

            # 7. Armazena os dados da parcela
            lista_parcelas.append(
                Parcela(
                    numero_parcela,
                    amortizacao_mes,
                    juros_mes,
                    valor_parcela,
                    saldo_devedor
                )
            )

        return SimulacaoResultado(lista_parcelas)

