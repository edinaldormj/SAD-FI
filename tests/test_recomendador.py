import os
import sys

# Ajuste do path para importar src/
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from domain.recomendador import RecomendadorModalidade

def testar_recomendador():
    recomendador = RecomendadorModalidade()

    # Cenário 1: Modalidade 1 é mais vantajosa
    msg1 = (
        "Modalidade 1 é mais vantajosa.\n"
        "Economia de R$ 15.000,00 (5.00%) em relação à Modalidade 2."
    )
    recomendacao1 = recomendador.recomendar({"mensagem_comparacao": msg1})
    print("🔍 Recomendação 1:", recomendacao1)
    assert "SAC fixo" in recomendacao1

    # Cenário 2: Modalidade 2 é mais vantajosa
    msg2 = (
        "Modalidade 2 é mais vantajosa.\n"
        "Economia de R$ 20.000,00 (7.00%) em relação à Modalidade 1."
    )
    recomendacao2 = recomendador.recomendar({"mensagem_comparacao": msg2})
    print("🔍 Recomendação 2:", recomendacao2)
    assert "SAC IPCA+" in recomendacao2

    # Cenário 3: Empate
    msg3 = "As duas modalidades apresentam o mesmo custo total. Nenhuma vantagem clara."
    recomendacao3 = recomendador.recomendar({"mensagem_comparacao": msg3})
    print("🔍 Recomendação 3:", recomendacao3)
    assert "Nenhuma recomendação" in recomendacao3

    print("✅ Todos os testes do RecomendadorModalidade passaram com sucesso.")

if __name__ == "__main__":
    testar_recomendador()
