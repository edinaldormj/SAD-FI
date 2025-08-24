import os
import sys
import tempfile

# Garante que o diretório 'src' esteja no sys.path para imports relativos ao projeto
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Importa a função que testaremos
from infrastructure.data.leitor_bancos import carregar_bancos_csv

def _write(tmpdir, name, text):
    """
    Função auxiliar para criar arquivos temporários de fixture.
    Retorna o caminho completo do arquivo criado.
    """
    p = os.path.join(tmpdir, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p

def testar_csv_valido(tmpdir):
    """
    Caso feliz: CSV com 3 bancos, variações de caixa, sistema em diferentes formatos.
    Verifica:
      - retorno é lista
      - quantidade de bancos carregados
      - normalização de 'sistema' para 'SAC_IPCA' (ex.: 'SAC_IPCA' vs 'sac')
    """
    print("\n🔧 CSV válido")
    content = """nome,sistema,taxa_anual
    Banco A,SAC,0.12
    Banco B,SAC_IPCA,0.085
    Banco C,sac,0.10
    """
    p = _write(tmpdir, "bancos_ok.csv", content)
    bancos = carregar_bancos_csv(p)
    print("✅ carregado:", bancos)
    assert len(bancos) == 3
    # Verifica que a segunda entrada foi normalizada para 'SAC_IPCA'
    assert bancos[1]["sistema"] == "SAC_IPCA"

def testar_csv_invalido_colunas(tmpdir):
    """
    CSV com colunas faltando — espera-se que a função lance uma Exception
    com mensagem informando colunas obrigatórias ausentes.
    """
    print("\n🔧 Colunas faltando")
    content = """nome,sistema
    Banco A,SAC
    """
    p = _write(tmpdir, "bancos_bad_cols.csv", content)
    try:
        carregar_bancos_csv(p)
        raise AssertionError("❌ era esperado erro por colunas faltando")
    except Exception as e:
        print("✅ erro esperado:", e)

def testar_csv_taxa_invalida(tmpdir):
    """
    CSV com taxa não numérica — a função deve lançar um erro.
    """
    print("\n🔧 Taxa inválida (não numérica)")
    content = """nome,sistema,taxa_anual
    Banco A,SAC,abc
    """
    p = _write(tmpdir, "bancos_bad_taxa.csv", content)
    try:
        carregar_bancos_csv(p)
        raise AssertionError("❌ era esperado erro por taxa inválida")
    except Exception as e:
        print("✅ erro esperado:", e)

def testar_csv_sistema_invalido(tmpdir):
    """
    CSV com sistema que não é SAC nem SAC_IPCA — espera erro descritivo.
    """
    print("\n🔧 Sistema inválido")
    content = """nome,sistema,taxa_anual
    Banco A,PRICE,0.1
    """
    p = _write(tmpdir, "bancos_bad_sistema.csv", content)
    try:
        carregar_bancos_csv(p)
        raise AssertionError("❌ era esperado erro por sistema inválido")
    except Exception as e:
        print("✅ erro esperado:", e)

def testar_csv_vazio(tmpdir):
    """
    Arquivo vazio deve resultar em erro (CSV sem cabeçalho).
    """
    print("\n🔧 CSV vazio")
    content = ""
    p = _write(tmpdir, "bancos_vazio.csv", content)
    try:
        carregar_bancos_csv(p)
        raise AssertionError("❌ era esperado erro por CSV vazio")
    except Exception as e:
        print("✅ erro esperado:", e)

if __name__ == "__main__":
    """
    Execução como script principal:
      - cria um diretório temporário
      - gera os arquivos de teste e executa cada caso
      - imprime status para facilitar leitura humana
    """
    print("🚀 Testes LeitorBancos")

    # Temporário: todos os arquivos de fixture são escritos em um diretório temporário
    with tempfile.TemporaryDirectory() as tmp:
        # Chamadas de teste recebem o caminho do diretório temporário
        testar_csv_valido(tmp)
        testar_csv_invalido_colunas(tmp)
        testar_csv_taxa_invalida(tmp)
        testar_csv_sistema_invalido(tmp)
        testar_csv_vazio(tmp)

    print("🎯 OK")
