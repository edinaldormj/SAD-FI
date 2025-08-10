import os
import pandas as pd
from datetime import datetime

def exportar_cronograma_csv(df: pd.DataFrame, nome_base: str, pasta_resultados: str = "resultados") -> str:
    """
    Exporta um DataFrame de cronograma para um arquivo CSV.

    Parâmetros:
        df (pandas.DataFrame): DataFrame com o cronograma da simulação.
        nome_base (str): Nome base do arquivo, sem extensão.
        pasta_resultados (str): Pasta onde o arquivo será salvo.

    Retorno:
        str: Caminho completo do arquivo CSV gerado.
    """
    if df.empty:
        raise ValueError("DataFrame vazio: não é possível exportar.")

    # Garante que a pasta existe
    os.makedirs(pasta_resultados, exist_ok=True)

    # Nome do arquivo com timestamp para evitar sobrescrita
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    nome_arquivo = f"{nome_base}_{timestamp}.csv"

    caminho_arquivo = os.path.join(pasta_resultados, nome_arquivo)

    # Exporta com separador ';' e encoding UTF-8 BOM (compatível com Excel)
    df.to_csv(caminho_arquivo, sep=";", index=False, encoding="utf-8-sig")

    return caminho_arquivo
