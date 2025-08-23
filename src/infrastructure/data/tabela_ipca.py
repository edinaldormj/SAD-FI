from infrastructure.data.leitor_csv import ler_csv

class TabelaIPCA:
    """
    Responsável por carregar e fornecer os valores mensais do IPCA
    a partir de um arquivo CSV já tratado.

    Utilizada pelos simuladores para calcular os juros variáveis indexados à inflação.
    """

    def __init__(self, caminho_csv: str):
        """
        Inicializa a tabela IPCA lendo os dados do arquivo.

        Parâmetros:
        caminho_csv (str): Caminho para o arquivo CSV contendo os dados do IPCA.
        """
        self.tabela = ler_csv(caminho_csv)

    def get_ipca(self, mes: int) -> float:
        """
        Retorna o valor percentual do IPCA correspondente ao mês do financiamento.

        Parâmetros:
        mes (int): Número do mês no financiamento (1 para o primeiro, 2 para o segundo, etc.)

        Retorno:
        float: Valor do IPCA em formato decimal (ex: 0.0042 para 0,42%)

        Exceção:
        IndexError: Se o mês solicitado for inválido.
        """
        if mes < 1 or mes > len(self.tabela):
            raise IndexError(f"Mês {mes} fora do intervalo disponível (1 a {len(self.tabela)})")
        return self.tabela.loc[mes - 1, "ipca"] / 100  # converte de % para decimal
    
    @classmethod
    def from_dataframe(cls, df):
        """
        Constrói uma TabelaIPCA a partir de um pandas.DataFrame.

        - Aceita DataFrame cujo campo de interesse seja 'ipca' (ou 'valor').
        - Detecta se os valores estão em FRAÇÃO (ex.: 0.005) ou em PERCENTUAL (ex.: 0.5).
          Regra: se max(abs(ipca)) <= 1.0 assume-se FRAÇÃO -> converte para % multiplicando por 100.
        - Normaliza ordenação por 'data' se coluna presente (tenta parse de datas).
        - Valida: coluna presente, sem NaN, valores numéricos.
        - Armazena internamente em % (mesmo formato que o construtor via CSV).
        """
        import pandas as pd

        if not isinstance(df, pd.DataFrame):
            raise TypeError("from_dataframe espera um pandas.DataFrame")

        df2 = df.copy()

        # aceitar nomes alternativos
        cols = [c.lower() for c in df2.columns]
        # normalizar colnames para facilitar (manter original também ok)
        if "ipca" not in cols and "valor" in cols:
            # renomear coluna 'valor' -> 'ipca'
            orig = df2.columns[cols.index("valor")]
            df2 = df2.rename(columns={orig: "ipca"})
        # agora exigimos 'ipca'
        if "ipca" not in [c.lower() for c in df2.columns]:
            raise ValueError("DataFrame precisa conter a coluna 'ipca' (ou 'valor')")

        # garantir que a coluna se chama exatamente 'ipca' (minúscula)
        # mapeia o nome real para 'ipca' se for 'IPCA' ou 'IpCa' etc.
        real_ipca_col = next(c for c in df2.columns if c.lower() == "ipca")
        # converter para numérico (erro se não for possível)
        df2[real_ipca_col] = pd.to_numeric(df2[real_ipca_col], errors="raise")

        # verificar NaN
        if df2[real_ipca_col].isna().any():
            raise ValueError("DataFrame contém NaN na coluna 'ipca'")

        # detectar unidade de forma robusta:
        # - se max_abs <= 0.02 (2%) --> assumimos FRAÇÃO (ex.: 0.005 -> 0.5%) e multiplicamos por 100
        # - caso contrário assumimos que já está em PERCENTUAL (ex.: 0.5 = 0.5%) e mantemos
        max_abs = df2[real_ipca_col].abs().max()
        if max_abs <= 0.02:
            # valores muito pequenos: eram fração -> converter para %
            df2[real_ipca_col] = df2[real_ipca_col] * 100.0
        # else: já está em %, mantemos como está


        # ordenar por data se houver coluna 'data' (tenta parse)
        if "data" in [c.lower() for c in df2.columns]:
            
            # parsing robusto de data: tenta formatos comuns antes de recorrer ao parser genérico
            real_data_col = next(c for c in df2.columns if c.lower() == "data")
            formats = ["%Y-%m-%d", "%Y-%m", "%m/%Y", "%d/%m/%Y"]
            parsed = None
            for fmt in formats:
                parsed_try = pd.to_datetime(df2[real_data_col], format=fmt, errors="coerce", dayfirst=True)
                if parsed_try.notna().any():
                    parsed = parsed_try
                    break
            if parsed is None:
                # fallback: permite dateutil (poderá emitir warning)
                parsed = pd.to_datetime(df2[real_data_col], dayfirst=True, errors="coerce")
            
            
            if parsed.isna().all():
                # se falhar no parse, não ordena, apenas mantém ordem original
                pass
            else:
                df2["_data_parsed_for_sort"] = parsed
                df2 = df2.sort_values("_data_parsed_for_sort").drop(columns=["_data_parsed_for_sort"])

        # reset index e manter apenas as colunas relevantes (preservamos 'ipca' coluna)
        df2 = df2.reset_index(drop=True)

        # criar instância sem chamar __init__ (evita ler CSV)
        inst = object.__new__(cls)
        inst.tabela = df2  # armazena DataFrame com coluna 'ipca' em %
        return inst
