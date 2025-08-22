import csv
import os

# Colunas que são obrigatórias no CSV de bancos
COLS_OBRIG = ["nome", "sistema", "taxa_anual"]

# Normalizamos os valores de sistema para estas duas opções válidas.
# Aceitamos variações de caixa e hífen (ex.: "sac", "SAC-ipca") e convertemos para underscore.
SISTEMAS_VALIDOS = {"SAC", "SAC_IPCA"}


def _normalizar_sistema(valor: str) -> str:
    """
    Normaliza a string do campo 'sistema' do CSV:
      - Trata None como string vazia
      - Remove espaços nas extremidades
      - Converte para UPPER CASE
      - Substitui '-' por '_' para permitir 'SAC-IPCA' e 'SAC_IPCA'
    Retorna a string normalizada (ex.: "SAC", "SAC_IPCA") ou "" se inválida.
    """
    if valor is None:
        return ""
    v = str(valor).strip().upper().replace("-", "_")
    return v


def carregar_bancos_csv(caminho_csv: str):
    """
    Lê e valida 'dados/bancos.csv'.

    Regras esperadas do arquivo:
      - Deve existir o arquivo no caminho informado (FileNotFoundError caso contrário)
      - Deve ter cabeçalho com, no mínimo, as colunas: nome, sistema, taxa_anual
      - `sistema` deve ser 'SAC' ou 'SAC_IPCA' (case-insensitive; aceita '-' e '_' e faz normalização)
      - `taxa_anual` deve estar em FRAÇÃO (ex.: 0.085 = 8.5% a.a.) e ser 0 < x < 1
      - Linhas totalmente em branco são ignoradas
      - Retorna uma lista de dicts com chaves normalizadas: {"nome", "sistema", "taxa_anual"}

    Observações implementacionais:
      - Abrimos com encoding "utf-8-sig" para suportar arquivos salvos do Excel que trazem BOM.
      - Substituímos vírgula por ponto em 'taxa_anual' para aceitar formatos locais como "0,085".
      - As mensagens de erro tentam ser informativas (incluem o número aproximado da linha).
    """
    # Verifica existência do arquivo
    if not os.path.isfile(caminho_csv):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_csv}")

    linhas = []  # lista que conterá os bancos válidos encontrados

    # Abrimos o CSV com newline="" e encoding que tolera BOM (utf-8-sig)
    # DictReader fornece um dicionário por linha com chaves do cabeçalho
    with open(caminho_csv, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        # Se o arquivo não tem cabeçalho, fieldnames = None -> erro
        if reader.fieldnames is None:
            raise ValueError("CSV vazio ou sem cabeçalho.")

        # Limpeza simples dos nomes de colunas (remove espaços)
        fields = [c.strip() for c in reader.fieldnames]

        # Valida se todas as colunas obrigatórias estão presentes
        faltando = [c for c in COLS_OBRIG if c not in fields]
        if faltando:
            raise ValueError(f"CSV inválido: faltam colunas obrigatórias: {faltando}")

        # Percorre as linhas do CSV
        for row in reader:
            # Se a linha for totalmente em branco (por exemplo, linhas extras no final), pular
            if not any(v and str(v).strip() for v in row.values()):
                continue

            # Faz validações e conversões por campo, envolvidas em try para gerar mensagem útil
            try:
                # Nome do banco — deve existir e não ser vazio
                nome = str(row["nome"]).strip()
                if not nome:
                    raise ValueError("Campo 'nome' vazio.")

                # Sistema — normaliza e valida contra as opções permitidas
                sistema = _normalizar_sistema(row["sistema"])
                if sistema not in SISTEMAS_VALIDOS:
                    # Mensagem explícita para facilitar correção do CSV pelo usuário
                    raise ValueError(f"Sistema inválido: {row.get('sistema')!r}. Use SAC ou SAC_IPCA.")

                # Taxa anual — aceita vírgula decimal; converte para float
                taxa_raw = str(row["taxa_anual"]).strip().replace(",", ".")
                taxa_anual = float(taxa_raw)

                # Verifica intervalo plausível: FRAÇÃO > 0 e < 1
                # (evita que o usuário insira 8.5 em vez de 0.085)
                if not (0.0 < taxa_anual < 1.0):
                    raise ValueError(f"taxa_anual deve estar em fração (0 < x < 1). Recebido: {taxa_raw}")

                # Se passou nas validações, adiciona à lista de resultados com formato estável
                linhas.append({"nome": nome, "sistema": sistema, "taxa_anual": taxa_anual})

            except ValueError as e:
                # O número da linha informado na mensagem é aproximado e pensado para ser útil ao usuário.
                # len(linhas) conta as linhas válidas já acumuladas; somando 2 aproximamos o índice real
                # (1 para cabeçalho + 1 para a linha atual em 1-based).
                raise ValueError(f"Erro na linha {len(linhas) + 2}: {e}")

    # Se não foi encontrado nenhum banco válido, sinalizamos erro
    if not linhas:
        raise ValueError("Nenhum banco válido encontrado no CSV (vazio?).")

    return linhas
