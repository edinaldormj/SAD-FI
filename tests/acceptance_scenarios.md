# Cenários de Aceitação — Sprint 3

## C1 — Simulação com IPCA via CSV
Dado `bancos.csv` válido e `ipca_tratado.csv` (IPCA em %)
Quando executo a simulação
Então vejo ranking por `total_pago` e recomendação
E existem `resultados/ranking.csv` e `resultados/ranking.png`

## C2 — Simulação com IPCA via BACEN 433 (24m)
Dado `bancos.csv` válido e conexão com o BACEN
Quando executo a simulação (fonte=BACEN, meses=24)
Então vejo ranking e recomendação
E evidências são geradas

## C3 — CSV de bancos inválido
Dado `bancos.csv` sem a coluna `taxa_anual`
Quando valido bancos
Então recebo mensagem amigável explicando o formato esperado

## C4 — Fallback de UI
Dado que a UI não está pronta
Quando uso a CLI + Notebook
Então as evidências são geradas e a recomendação é exibida
