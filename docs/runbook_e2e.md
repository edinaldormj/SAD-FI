# Runbook E2E (demo e defesa)

1) Entradas:
   - `valor_total=500000`, `entrada=50000`, `prazo_anos=30`
   - `dados/bancos.csv` (3–5 bancos de exemplo)
   - IPCA: BACEN 433 (24 meses) **ou** `dados/ipca_tratado.csv`

2) Passos:
   - Validar bancos → Validar IPCA → Simular
   - Gerar ranking e recomendação
   - Exportar CSV/PNG

3) Verificações:
   - `resultados/ranking.csv` existe e tem colunas corretas
   - `resultados/ranking.png` mostra barras horizontais ordenadas
   - Mensagem: “Recomendação: …”

4) Plano B:
   - Se BACEN cair: usar CSV de IPCA offline
   - Se UI atrasar: CLI + Notebook
