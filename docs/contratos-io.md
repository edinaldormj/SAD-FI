# Contratos de Entrada/Saída — Sprint 3

## Entradas (usuário)
- `valor_total`: número > 0 (BRL)
- `entrada`: número >= 0 (BRL)
- `prazo_anos`: inteiro > 0
- `bancos.csv`: colunas **nome,sistema,taxa_anual**
  - `sistema` ∈ {SAC, SAC_IPCA}
  - `taxa_anual` em **fração** (0.085 = 8,5% a.a.)
- **Fonte do IPCA**:
  - **CSV local**: `dados/ipca_tratado.csv` (colunas `data (YYYY-MM)`, `ipca` em **%** mensal)
  - **BACEN 433**: janela padrão **24** meses (configurável)

## Saídas (evidências)
- `resultados/ranking.csv`
  - colunas: `banco;modalidade;total_pago;total_juros;num_parcelas`
- `resultados/ranking.png`
  - gráfico de barras **horizontal** ordenado (top vencedor em destaque)
- Mensagem de recomendação (texto):
  - “Recomendação: <Banco> – <Modalidade> com menor custo total.”

## Regras
- IPCA armazenado em **%**; consumo em **fração** via `get_ipca(m)`.
- Ranking ordenado por `total_pago` (crescente). Empates → estáveis.
