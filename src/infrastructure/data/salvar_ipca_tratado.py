import pandas as pd

def salvar_csv_tratado(entrada: str, saida: str = "dados/ipca_tratado.csv") -> None:
    """
    Lê o CSV original do IPCA no padrão BACEN, trata os dados e salva como novo CSV.

    Parâmetros:
    entrada (str): Caminho para o arquivo IPCA original (ex: dados/ipca.csv)
    saida (str): Caminho de saída para o CSV tratado (default: dados/ipca_tratado.csv)
    """
    df = pd.read_csv(entrada, encoding="ISO-8859-1", sep=None, engine="python")

    # Renomeia colunas
    df = df.rename(columns={
        df.columns[0]: "data",
        df.columns[1]: "ipca"
    })

    # Remove linha com a fonte (se existir)
    df = df[~df["data"].astype(str).str.contains("Fonte", case=False, na=False)]

    # Substitui vírgula por ponto e remove espaços
    df["ipca"] = df["ipca"].astype(str).str.replace(",", ".").str.strip()

    # Remove vazios e converte
    df = df[df["ipca"] != ""]
    df["ipca"] = df["ipca"].astype(float)

    df = df.reset_index(drop=True)
    df.to_csv(saida, sep=";", index=False, encoding="utf-8")
    print(f"✅ Arquivo tratado salvo em: {saida}")

# Execução direta (opcional)
if __name__ == "__main__":
    salvar_csv_tratado("dados/ipca.csv")