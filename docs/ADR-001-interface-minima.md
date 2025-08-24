# ADR-001 — Interface mínima e fallback (Sprint 3)

## Contexto
Precisamos entregar simulação **multi-bancos** (SAC e SAC_IPCA) com **ranking** e **recomendação**. O público é leigo; a entrega precisa ser reprodutível.

## Decisão
**Plano A (preferido):** UI mínima visual  
- Entradas: `valor_total`, `entrada`, `prazo_anos`, `bancos.csv`, fonte do IPCA (CSV ou BACEN 433 + meses).  
- Botão **Validar** (bancos e IPCA) e **Simular** (só habilita após validações).  
- Saídas: ranking em texto + gráfico simplificado + exportações (`resultados/ranking.csv` e `resultados/ranking.png`).

**Plano B (fallback se a UI atrasar):** CLI + Notebook  
- CLI coleta entradas e chama o Controlador; Notebook gera gráfico/exportações.  
- Critérios de aceite da Sprint **se mantêm**.

## Consequências
- Evitamos bloquear a entrega por causa da UI.  
- Notebook passa a depender do Controlador (sem duplicar regras do domínio).

## Status
Aprovado em Sprint 3 (data).

## Rationale
Entrega incremental, com foco em reprodutibilidade e evidências.

## Itens fora de escopo
- Estilo/branding avançado; pesos de critérios além de `total_pago`.

## Links
- Contratos de I/O  
- UX-mensagens
