# UX — Estados e Mensagens (PT-BR, tom simples)

## Validações
- **Bancos inválidos**: “O arquivo `bancos.csv` precisa ter as colunas `nome,sistema,taxa_anual` e valores válidos. Exemplos: SAC, SAC_IPCA; taxa em fração (0.085 = 8,5% a.a.).”
- **Fonte IPCA ausente**: “Escolha uma fonte de IPCA: CSV local ou BACEN (série 433).”
- **IPCA CSV inválido**: “O IPCA deve ter colunas `data (YYYY-MM)` e `ipca` em **%**. Verifique o arquivo e tente novamente.”
- **BACEN indisponível**: “Não foi possível acessar a série 433 agora. Tente novamente mais tarde ou use um CSV local.”
- **Parâmetros inválidos**: “Preencha `valor_total`, `entrada` (opcional) e `prazo_anos` com números válidos.”

## Ações
- **Validar (bancos/IPCA)**: “Validação concluída. Você pode clicar em **Simular**.”
- **Simular**: “Simulação em andamento… isso pode levar alguns segundos.”

## Resultados
- **Ranking**: “Vencedor: <Banco> – <Modalidade>. Custo total: R$ X.”
- **Exportações**: “Evidências salvas em `./resultados` (CSV e PNG).”
