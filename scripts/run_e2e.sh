#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.."; pwd -P)"
export PYTHONPATH="src"

echo "== SAD-FI E2E offline =="
echo "→ pytest -q"
pytest -q

echo "→ Simulando multi-bancos + exportando evidências..."
python scripts/e2e_runner.py \
  --bancos "dados/bancos.csv" \
  --ipca "dados/txjuros/IPCA_BACEN.csv" \
  --tr "dados/txjuros/TR_mensal_compat.csv" \
  --valor-total 300000 --entrada 60000 --prazo-anos 30 --taxa 0.11

echo "✓ E2E concluído com sucesso."
