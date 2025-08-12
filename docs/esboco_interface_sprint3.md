# Esboço de Interface – Sprint 3 (SAD-FI)

## Objetivo
Guiar a implementação da UI na Sprint 3, com base no fluxo de uso e nas necessidades funcionais levantadas na Sprint 2.

## Entradas do Usuário
- Valor do imóvel (R$), Entrada (R$)
- Prazo (anos ou meses)
- Sistema: SAC fixo | SAC + IPCA
- Taxa anual (a.a.) para o sistema escolhido
- Para SAC + IPCA: caminho do CSV de IPCA
- Opções: gerar gráfico, exportar CSV, nome da simulação

## Saídas / Exibição
- Resumo por modalidade (custo total, juros, parcelas)
- Comparação (dif. abs/%, interpretação)
- Recomendação final
- Gráficos (custo total; opcionalmente evolução mensal)
- Exportação CSV e mensagens/avisos

## Fluxo (Entrada → Processamento → Resultado)
1. Usuário informa parâmetros e valida.
2. Sistema executa simulações, compara e recomenda.
3. Tela de resultados exibe resumos, gráficos e exportação.

## Wireframes (texto)
### Tela de Parâmetros
- Campos de entrada conforme seção “Entradas”
- Botão [Simular], opção de limpar, área de mensagens

### Tela de Resultados
- Resumos por modalidade
- Bloco de comparação + recomendação
- Gráfico de custo total por modalidade
- Botão [Exportar CSV] e indicação de arquivo gerado
- Área de avisos (IPCA negativo, dados ausentes, etc.)

## Observações de UX
- Validações inline (exibir mensagem ao lado do campo)
- Padrões de formato numérico (R$ e %)
- Feedback de carregamento ao simular
- Acessibilidade básica (labels, foco, teclas)

## Arquivos relacionados
- `docs/wireframes/ui_flow.puml` – diagrama do fluxo
- `notebooks/01_visualizacao_simulacao.ipynb` – referência de gráficos
