## UI (offline) — Comparação SAC, SAC TR e SAC IPCA

**Objetivo:** executar a comparação a partir de CSVs locais, exibindo ranking, mensagem de recomendação e gráfico do Top-3.

### Pré-requisitos
- Python 3.10+
- Dependências:
```bash
pip install -r requirements.txt
# se necessário:
pip install streamlit matplotlib pandas
```
---

## Arquivos de dados esperados

- `dados/bancos.csv` — ofertas de bancos (ver template no repositório).

- `dados/txjuros/IPCA_BACEN.csv` — série mensal no formato data,ipca (percentual ou fração).

- `dados/txjuros/TR_mensal_compat.csv` — série mensal no formato data,tr.

## Como executar a UI

```bash
streamlit run src/presentation/ui_app.py
```
Informar na tela: valor do imóvel, entrada, prazo em anos, taxa base anual, e caminhos dos arquivos.


