import os, sys, tempfile
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from application.controlador import ControladorApp

def testar_erro_ipca_ausente():
    content = "nome,sistema,taxa_anual\nBanco IPCA,SAC_IPCA,0.09\n"
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "bancos_ipca.csv")
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        ctrl = ControladorApp()
        try:
            # fonte_ipca = None -> espera KeyError (ou RuntimeError conforme sua implementação)
            ctrl.simular_multiplos_bancos(p, {"valor_total":100000,"entrada":10000,"prazo_anos":10}, fonte_ipca=None)
        except Exception as e:
            print("Erro esperado:", type(e).__name__, str(e))
            return
        raise AssertionError("Esperado erro quando banco SAC_IPCA e fonte_ipca é None")

if __name__ == "__main__":
    testar_erro_ipca_ausente()
    print("OK")
