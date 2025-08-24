import os, sys, logging

# 1) Preparar PATH e logs
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC  = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

print("🔧 Smoke de integração: Controlador + (TR/IPCA)")

# 2) Imports
from application.controlador import ControladorApp
from infrastructure.data.leitor_bancos import carregar_bancos_csv

# 3) Entradas
caminho_bancos = os.path.join(ROOT, 'dados', 'bancos.csv')
bancos = carregar_bancos_csv(caminho_bancos)
has_ipca = any(b['sistema'].upper() == 'SAC_IPCA' for b in bancos)
has_tr   = any(b['sistema'].upper() == 'SAC_TR'   for b in bancos)

# Fonte IPCA (se houver SAC_IPCA no CSV)
fonte_ipca = {"caminho_ipca": os.path.join(ROOT, "dados", "ipca_360.csv")} if has_ipca else None
# Fonte TR (fixture local) — ajuste o caminho se necessário
fonte_tr = {"fixture_csv_path": os.path.join(ROOT, "tests", "fixtures", "tr_fixture.csv")} if has_tr else None

# Dados do financiamento (exemplo)
dados = {
    "valor_total": 300_000.00,
    "entrada":     60_000.00,
    "prazo_anos":  30,
    "taxa_juros_anual": 0.11,   # taxa base usada no simulador
}

# 4) Execução
print(f"📄 bancos.csv: {caminho_bancos}")
print(f"🔎 SAC_IPCA no CSV? {has_ipca} | SAC_TR no CSV? {has_tr}")

ctrl = ControladorApp()
resultados, ranking, mensagem = ctrl.simular_multiplos_bancos(
    caminho_bancos_csv=caminho_bancos,
    dados_financiamento=dados,
    fonte_ipca=fonte_ipca,
    fonte_tr=fonte_tr,
)

# 5) Evidências no terminal
print("\n🏁 Ranking (menor total → maior):")
for rotulo, total in ranking:
    print(f" - {rotulo}: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

print("\n📣 Recomendação:")
print(mensagem)

print("\n✅ Smoke de integração concluído.")
