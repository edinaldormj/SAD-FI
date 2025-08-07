import pandas as pd

def ler_csv(caminho: str) -> pd.DataFrame:
    """
    Lê e trata o CSV do IPCA proveniente do BACEN.

    Etapas:
    - Renomeia colunas para 'data' e 'ipca'
    - Remove linha final com a fonte (se existir)
    - Converte vírgula decimal para ponto
    - Remove entradas inválidas ou vazias
    - Converte IPCA para float
    """
    df = pd.read_csv(caminho, encoding="ISO-8859-1", sep=None, engine="python")
    print(df.head())  # verificar se veio algo
    # Renomeia colunas para nomes tratáveis
    df = df.rename(columns={
        df.columns[0]: "data",
        df.columns[1]: "ipca"
    })

    # Remove linha com a fonte (se presente)
    df = df[~df["data"].astype(str).str.contains("Fonte", case=False, na=False)]

    # Substitui vírgula por ponto, remove espaços e converte
    df["ipca"] = df["ipca"].astype(str).str.replace(",", ".").str.strip()

    # Remove linhas em branco ou vazias
    df = df[df["ipca"] != ""]
    df["ipca"] = df["ipca"].astype(float)

    # Reinicia índice
    df = df.reset_index(drop=True)
    return df

if __name__ == "__main__":
    df = ler_csv("dados/ipca.csv")
    print(df.head())
