import os
import sys

# Garante que src/ esteja no sys.path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from infrastructure.data.leitor_bancos import carregar_bancos_csv

# 📂 Caminho para fixtures (ajuste se necessário)
CSV_VALIDO = "dados/bancos_exemplo.csv"
CSV_INVALIDO = "dados/bancos_invalido.csv"
CSV_VAZIO = "dados/bancos_vazio.csv"


def testar_csv_valido():
    print("\n🔧 Testando CSV válido...")
    bancos = carregar_bancos_csv(CSV_VALIDO)
    print("✅ Bancos carregados:", bancos)
    assert isinstance(bancos, list)
    assert len(bancos) > 0
    for b in bancos:
        assert "nome" in b and "sistema" in b and "taxa_anual" in b


def testar_csv_invalido_colunas():
    print("\n🔧 Testando CSV inválido (colunas faltando)...")
    try:
        carregar_bancos_csv(CSV_INVALIDO)
    except Exception as e:
        print("✅ Erro esperado:", e)
        assert "coluna" in str(e).lower() or "falt" in str(e).lower()
    else:
        raise AssertionError("❌ Era esperado erro por colunas faltando")


def testar_csv_vazio():
    print("\n🔧 Testando CSV vazio...")
    try:
        carregar_bancos_csv(CSV_VAZIO)
    except Exception as e:
        print("✅ Erro esperado:", e)
        assert "vazio" in str(e).lower() or "nenhum" in str(e).lower()
    else:
        raise AssertionError("❌ Era esperado erro por CSV vazio")


def testar_csv_sistema_invalido():
    print("\n🔧 Testando CSV com sistema inválido...")
    linhas = [
        "nome,sistema,taxa_anual",
        "Banco X,INVALIDO,0.1"
    ]
    tmp_path = "dados/bancos_tmp.csv"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    try:
        carregar_bancos_csv(tmp_path)
    except Exception as e:
        print("✅ Erro esperado:", e)
        assert "sistema" in str(e).lower() or "inválido" in str(e).lower()
    else:
        raise AssertionError("❌ Era esperado erro por sistema inválido")
    finally:
        os.remove(tmp_path)


def testar_csv_taxa_invalida():
    print("\n🔧 Testando CSV com taxa inválida...")
    linhas = [
        "nome,sistema,taxa_anual",
        "Banco Y,SAC,abc"
    ]
    tmp_path = "dados/bancos_tmp.csv"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    try:
        carregar_bancos_csv(tmp_path)
    except Exception as e:
        print("✅ Erro esperado:", e)
        assert "taxa" in str(e).lower() or "float" in str(e).lower()
    else:
        raise AssertionError("❌ Era esperado erro por taxa inválida")
    finally:
        os.remove(tmp_path)


if __name__ == "__main__":
    print("🚀 Iniciando testes de Leitor de Bancos CSV")
    testar_csv_valido()
    testar_csv_invalido_colunas()
    testar_csv_vazio()
    testar_csv_sistema_invalido()
    testar_csv_taxa_invalida()
    print("✅ Todos os testes de Leitor de Bancos CSV passaram com sucesso.")
