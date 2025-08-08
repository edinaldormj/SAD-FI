class RecomendadorModalidade:
    """
    Classe responsável por gerar uma recomendação textual com base nos resultados
    de simulações de financiamento.

    A decisão é feita a partir de dados comparativos, atualmente baseando-se na
    mensagem textual produzida por `ComparadorModalidades`.

    A estrutura foi projetada para suportar expansão futura com critérios adicionais,
    como risco, volatilidade e perfil do usuário.
    """

    def recomendar(self, dados: dict) -> str:
        """
        Analisa os dados comparativos e retorna uma recomendação amigável.

        Parâmetros:
        - dados (dict): Deve conter, no mínimo:
            - 'mensagem_comparacao' (str): Texto retornado por `comparar()`

        Retorno:
        - str: Exemplo -> "💡 Recomendado: SAC IPCA+"
        """
        mensagem = dados.get("mensagem_comparacao", "")

        if "Modalidade 1 é mais vantajosa" in mensagem:
            return "💡 Recomendado: SAC fixo"
        elif "Modalidade 2 é mais vantajosa" in mensagem:
            return "💡 Recomendado: SAC IPCA+"
        else:
            return "💡 Nenhuma recomendação: ambas as modalidades apresentam custo equivalente"

