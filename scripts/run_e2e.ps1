Param(
  [string]$Bancos = "dados/bancos.csv",
  [string]$IPCA   = "dados/txjuros/IPCA_BACEN.csv",
  [string]$TR     = "dados/txjuros/TR_mensal_compat.csv",
  [double]$Valor  = 300000.0,
  [double]$Entrada = 60000.0,
  [int]$PrazoAnos = 30,
  [double]$Taxa   = 0.11
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Write-Host "== SAD-FI E2E offline =="

# Garantir PYTHONPATH
$env:PYTHONPATH = "src"

# 1) Testes
Write-Host "-> Running tests (pytest -q)..."
pytest -q
if ($LASTEXITCODE -ne 0) { Write-Error "Tests failed."; exit 10 }

# 2) Simulacao + export de evidencias
Write-Host "-> Simulating multi-banks and exporting artifacts..."
python "scripts/e2e_runner.py" `
  --bancos "$Bancos" `
  --ipca "$IPCA" `
  --tr "$TR" `
  --valor-total $Valor `
  --entrada $Entrada `
  --prazo-anos $PrazoAnos `
  --taxa $Taxa

if ($LASTEXITCODE -ne 0) { Write-Error "E2E runner failed."; exit 11 }

Write-Host "OK - E2E completed successfully."
