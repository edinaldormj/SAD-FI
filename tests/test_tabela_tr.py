import os
import sys

# inclui src/ no sys.path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print("🔧 Iniciando smoke de TabelaTR")
print("📁 Caminho src/ adicionado ao sys.path")

try:
    import pandas as pd
    from infrastructure.data.tabela_tr import TabelaTR
    print("✅ Importações bem-sucedidas")
except Exception as e:
    print(f"❌ Erro ao importar dependências: {e}")
    input("Pressione Enter para sair...")
    raise

def _teste_tabela_from_dataframe():
    print("[TEST] TabelaTR.from_dataframe — normalização básica")
    df = pd.DataFrame({
        "data": ["01/2024", "2024-02", "2024-03"],
        "tr":   [0.0, 0.04, 0.05],  # frações (4% e 5% seriam 0.04 e 0.05)
    })
    tab = TabelaTR.from_dataframe(df)
    datas = list(tab.df["data"])
    assert datas == ["2024-01", "2024-02", "2024-03"], f"Datas normalizadas incorretas: {datas}"
    assert abs(tab.taxa_mensal("2024-02") - 0.04) < 1e-12
    print("  ok")

def _teste_percentual_para_fracao():
    print("[TEST] Conversão de % para fração")
    # Exemplo em porcentagem (5 -> 5%) deve virar 0.05
    dfp = pd.DataFrame({
        "data": ["2024-01", "2024-02"],
        "tr":   [0.0, 5.0],  # porcentagem
    })
    tabp = TabelaTR.from_dataframe(dfp)
    assert abs(tabp.taxa_mensal("2024-02") - 0.05) < 1e-12
    print("  ok")

def _demo_prints():
    print("[DEMO] Uso básico em memória")
    df = pd.DataFrame({
        "data": ["2024-01", "2024-02", "2024-03"],
        "tr":   [0.0, 0.001, 0.002],  # 0.1% e 0.2%
    })
    tab = TabelaTR.from_dataframe(df)
    for ym in ["2024-01", "2024-02", "2024-03"]:
        print(f"  TR {ym}: {tab.taxa_mensal(ym):.6f}")

if __name__ == "__main__":
    try:
        _teste_tabela_from_dataframe()
        _teste_percentual_para_fracao()
        _demo_prints()
        print("✅ Smoke TabelaTR finalizado sem erros.")
    except AssertionError as e:
        print(f"❌ Falha: {e}")
    input("Pressione Enter para sair...")
