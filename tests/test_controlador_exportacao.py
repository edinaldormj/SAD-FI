import os
import re
import sys

# Ajuste do path para importar src/
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from application.controlador import ControladorApp

# Dependência apenas aqui no teste
import pandas as pd


class DummyResultadoOK:
    """Simula um SimulacaoResultado com to_dataframe() válido e não vazio."""
    def to_dataframe(self):
        return pd.DataFrame({
            "n_parcela": [1, 2],
            "data": ["2025-01-01", "2025-02-01"],
            "valor_parcela": [1000.0, 1000.0],
            "amortizacao": [500.0, 500.0],
            "juros": [500.0, 500.0],
            "saldo_devedor": [199000.0, 198000.0],
        })


class DummyResultadoVazio:
    """Simula um SimulacaoResultado cujo to_dataframe() retorna DF vazio."""
    def to_dataframe(self):
        return pd.DataFrame()


class DummySemToDataFrame:
    """Simula um objeto inválido, sem to_dataframe()."""
    pass


def testar_exportacao_ok():
    ctrl = ControladorApp()
    obj = DummyResultadoOK()

    caminho = ctrl.exportar_resultado(obj, "simulacao_teste")

    # 1) arquivo existe
    assert os.path.isfile(caminho), "CSV não foi gerado."

    # 2) está em resultados/
    assert os.path.basename(os.path.dirname(caminho)) == "resultados"

    # 3) padrão de nome: simulacao_teste_YYYY-MM-DD_HHMM.csv
    nome = os.path.basename(caminho)
    assert re.match(r"^simulacao_teste_\d{4}-\d{2}-\d{2}_\d{4}\.csv$", nome), f"Nome inesperado: {nome}"

    # 4) conteúdo do CSV
    df_lido = pd.read_csv(caminho, sep=";")
    assert list(df_lido.columns) == [
        "n_parcela", "data", "valor_parcela", "amortizacao", "juros", "saldo_devedor"
    ], "Cabeçalhos incorretos."
    assert len(df_lido) == 2, "Quantidade de linhas incorreta."

    print("🧪 [OK] Exportação CSV realizada com sucesso:", caminho)


def testar_exportacao_df_vazio():
    ctrl = ControladorApp()
    obj_vazio = DummyResultadoVazio()

    try:
        ctrl.exportar_resultado(obj_vazio, "simulacao_vazia")
        assert False, "Era esperado ValueError para DataFrame vazio."
    except ValueError as e:
        print("🧪 [OK] ValueError para DF vazio:", e)


def testar_exportacao_sem_to_dataframe():
    ctrl = ControladorApp()
    obj_invalido = DummySemToDataFrame()

    try:
        ctrl.exportar_resultado(obj_invalido, "qualquer")
        assert False, "Era esperado TypeError para objeto sem to_dataframe()."
    except TypeError as e:
        print("🧪 [OK] TypeError para objeto sem to_dataframe():", e)


if __name__ == "__main__":
    print("🔧 Iniciando testes de exportação CSV (ControladorApp)")
    testar_exportacao_ok()
    testar_exportacao_df_vazio()
    testar_exportacao_sem_to_dataframe()
    print("✅ Todos os testes passaram com sucesso.")
