# --- bootstrap de imports: garante que 'src' está no sys.path ---
import os
import sys
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # repo root
SRC  = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
# ---------------------------------------------------------------

from application.controlador import ControladorApp


def _normalize_modalidade(label: str):
    """
    Extrai/normaliza a modalidade a partir do rótulo, tolerando variações:
      - dashes: '-', '–', '—'
      - 'SAC TR', 'SAC-TR', 'SAC_TR'
      - 'SAC IPCA' e 'SAC IPCA+'
    Retorna: 'SAC', 'SAC_TR', 'SAC_IPCA' ou None.
    """
    if label is None:
        return None
    s = unicodedata.normalize("NFKC", str(label)).upper()
    # unifica separadores/hífens/underscores e espaços múltiplos
    s = s.replace("_", " ")
    s = re.sub(r"[\u2010-\u2015\-]+", "-", s)  # todos os dashes → '-'
    s = re.sub(r"\s+", " ", s).strip()

    # match mais específico primeiro
    if re.search(r"\bSAC\s*IPCA\+?\b", s):
        return "SAC_IPCA"
    if re.search(r"\bSAC\s*TR\b", s):
        return "SAC_TR"
    if re.search(r"\bSAC\b", s):
        return "SAC"
    return None


def test_e2e_offline_minimo():
    """
    E2E offline mínimo: usa CSVs locais reais (BCB/IPCA e TR compat) e um bancos.csv válido.
    Critérios:
      - ranking não vazio
      - totais > 0 e ordenados de forma crescente
      - mensagem não vazia
      - pelo menos 1 modalidade conhecida no rótulo
    """
    bancos = ROOT / "dados" / "bancos.csv"
    ipca   = ROOT / "dados" / "txjuros" / "IPCA_BACEN.csv"
    tr     = ROOT / "dados" / "txjuros" / "TR_mensal_compat.csv"

    assert bancos.exists(), f"Arquivo obrigatório ausente: {bancos}"
    assert ipca.exists(),   f"Arquivo obrigatório ausente: {ipca}"
    assert tr.exists(),     f"Arquivo obrigatório ausente: {tr}"

    resultados, ranking, msg = ControladorApp().simular_multiplos_bancos(
        caminho_bancos_csv=str(bancos),
        dados_financiamento={
            "valor_total": 300_000.0,
            "entrada": 60_000.0,
            "prazo_anos": 30,
            "taxa_juros_anual": 0.11,
        },
        fonte_ipca={"caminho_ipca": str(ipca)},
        fonte_tr={"fixture_csv_path": str(tr)},
    )

    # 1) ranking básico
    assert ranking, "Ranking vazio."
    assert all(tp > 0 for _, tp in ranking), "Há total <= 0 no ranking."

    # 2) ordenação crescente por Total Pago
    totals = [tp for _, tp in ranking]
    assert totals == sorted(totals), "Ranking não está em ordem crescente por Total Pago."

    # 3) mensagem presente
    assert isinstance(msg, str) and msg.strip(), "Mensagem vazia."

    # 4) pelo menos 1 modalidade conhecida no rótulo (robusta a variações)
    modalidades = {_normalize_modalidade(lbl) for lbl, _ in ranking}
    modalidades.discard(None)
    conhecidos = {"SAC", "SAC_TR", "SAC_IPCA"}
    assert modalidades.intersection(conhecidos), (
        "Nenhuma modalidade conhecida encontrada nos rótulos: "
        f"{[lbl for lbl, _ in ranking]}"
    )
