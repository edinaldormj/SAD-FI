import pandas as pd

def ler_csv(caminho):
    return pd.read_csv(caminho, sep=';', decimal=',')
