class ComparadorModalidades:
    """
    Classe responsável por comparar duas modalidades de financiamento
    (ex: SAC fixo vs. SAC IPCA+) com base em seus resultados simulados.
    """

    def comparar(self, resultado1, resultado2) -> str:
        """
        Compara dois objetos de simulação e retorna uma mensagem interpretável.

        Parâmetros:
        resultado1: Objeto SimulacaoResultado da modalidade 1.
        resultado2: Objeto SimulacaoResultado da modalidade 2.

        Retorno:
        str: Texto com interpretação da vantagem de uma modalidade sobre a outra.
        """
        total1 = resultado1.total_pago
        total2 = resultado2.total_pago

        diferenca = abs(total1 - total2)
        percentual = (diferenca / min(total1, total2)) * 100 if min(total1, total2) > 0 else 0

        if abs(total1 - total2) < 1e-2:
            return "As duas modalidades apresentam o mesmo custo total. Nenhuma vantagem clara."

        if total1 < total2:
            return (
                f"Modalidade 1 é mais vantajosa.\n"
                f"Economia de R$ {diferenca:,.2f} ({percentual:.2f}%) em relação à Modalidade 2."
            )
        else:
            return (
                f"Modalidade 2 é mais vantajosa.\n"
                f"Economia de R$ {diferenca:,.2f} ({percentual:.2f}%) em relação à Modalidade 1."
            )
