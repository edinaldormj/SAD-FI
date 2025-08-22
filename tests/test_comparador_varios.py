"""
tests/test_comparador_varios.py

Testes para application.comparador:
- comparar_varios(resultados)
- recomendar(ranking, modalidades, tol)

Estilo: prints + assert, conforme padrão do repositório.
"""

import os
import sys

# garante src no path para imports do projeto
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from application.comparador import comparar_varios, recomendar

# --- utilitários de teste ---------------------------------------------------

class DummyResult:
    """Objeto simples que expõe .total_pago como nos SimulacaoResultado."""
    def __init__(self, total_pago):
        self.total_pago = total_pago

def print_header(title: str):
    print("\n" + title)
    print("-" * len(title))

# --- casos de teste --------------------------------------------------------

def testar_ranking_basico():
    print_header("🔧 testar_ranking_basico")
    resultados = {
        "Banco A – SAC": DummyResult(1000.0),
        "Banco B – SAC IPCA+": DummyResult(900.0),
        "Banco C – SAC": DummyResult(1100.0),
    }

    ranking = comparar_varios(resultados)
    print("ranking:", ranking)
    # menor total deve ser Banco B
    assert ranking[0][0] == "Banco B – SAC IPCA+"
    msg = recomendar(ranking)
    print("mensagem:", msg)
    assert "Recomendação:" in msg and "Banco B" in msg

def testar_empate_estabilidade_e_tie_break():
    print_header("🔧 testar_empate_estabilidade_e_tie_break")
    # Dois bancos com valores muito próximos: ordenação secundária por rótulo (alfabética)
    # Usamos valores não exatamente iguais para poder testar a tolerância.
    resultados = {
        "B": DummyResult(500.000001),  # ligeiramente maior
        "A": DummyResult(500.0),       # ligeiramente menor
        "C": DummyResult(600.0),
    }

    ranking = comparar_varios(resultados)
    print("ranking (empate aproximado):", ranking)
    # por estabilidade, A deve aparecer antes de B se os totais fossem iguais;
    # aqui A tem menor total, portanto vem primeiro
    assert ranking[0][0] == "A" and ranking[1][0] == "B"

    # testar recomendação com tolerância muito estreita que NÃO considera empate técnico
    msg_no_empate = recomendar(ranking, tol=1e-9)
    print("mensagem (sem empate técnico):", msg_no_empate)
    assert "Recomendação" in msg_no_empate and "A" in msg_no_empate

    # testar empate técnico com tolerância maior (captura valores próximos como empate)
    msg_empate = recomendar(ranking, tol=1e-1)
    print("mensagem (empate técnico):", msg_empate)
    assert "Empate" in msg_empate or "Empate técnico" in msg_empate


def testar_modalidades_e_dict_like_results():
    print_header("🔧 testar_modalidades_e_dict_like_results")
    # suporte a dicionário no lugar de objeto (dict com chave 'total_pago')
    resultados = {
        "Banco X – SAC": {"total_pago": 2000.0},
        "Banco Y – SAC_IPCA": {"total_pago": 1800.0},
    }
    ranking = comparar_varios(resultados)
    print("ranking (dict-like):", ranking)
    assert ranking[0][0] == "Banco Y – SAC_IPCA"

    # testar mensagem que inclui modalidade quando fornecida
    modalidades = {
        "Banco Y – SAC_IPCA": "SAC IPCA+",
        "Banco X – SAC": "SAC"
    }
    msg = recomendar(ranking, modalidades=modalidades)
    print("mensagem com modalidades:", msg)
    assert "SAC IPCA+" in msg or "Banco Y" in msg

def testar_erro_sem_total():
    print_header("🔧 testar_erro_sem_total")
    class Bad:
        pass

    resultados = {"X": Bad()}
    try:
        comparar_varios(resultados)
    except ValueError as e:
        print("✅ erro esperado (sem total):", e)
    else:
        raise AssertionError("❌ Esperado ValueError quando total_pago não existe")

def testar_erro_total_nao_numerico():
    print_header("🔧 testar_erro_total_nao_numerico")
    resultados = {"Z": {"total_pago": "não-numérico"}}
    try:
        comparar_varios(resultados)
    except ValueError as e:
        print("✅ erro esperado (total não numérico):", e)
    else:
        raise AssertionError("❌ Esperado ValueError quando total_pago não é conversível para float")


# --- execução ---------------------------------------------------------------

if __name__ == "__main__":
    print("🚀 Executando testes do comparador")
    testar_ranking_basico()
    testar_empate_estabilidade_e_tie_break()
    testar_modalidades_e_dict_like_results()
    testar_erro_sem_total()
    testar_erro_total_nao_numerico()
    print("\n🎯 Todos os testes do comparador passaram (se nenhum assert falhou).")
