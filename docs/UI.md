## UI (offline) — Comparação SAC, SAC TR e SAC IPCA

**Objetivo:** executar a comparação a partir de CSVs locais, exibindo ranking, mensagem de recomendação e gráfico do Top-3.

### 1. Pré-requisitos
- Python 3.10+
- Dependências:
```bash
pip install -r requirements.txt
# se necessário:
pip install streamlit matplotlib pandas
```
---

### 2. Arquivos de dados esperados

- `dados/bancos.csv` — ofertas de bancos (ver template no repositório).

- `dados/txjuros/IPCA_BACEN.csv` — série mensal no formato data,ipca (percentual ou fração).

- `dados/txjuros/TR_mensal_compat.csv` — série mensal no formato data,tr.

---

### 3. Como executar a UI

```bash
streamlit run src/presentation/ui_app.py
```
- Informar na tela: 
   - valor do imóvel;
   - entrada;
   - prazo em anos;
   - taxa base anual; e
   - caminhos dos arquivos.

---

### 4. Evidências

- ```resultados/ranking.csv```
- ```resultados/graficos/ranking.png```

---

### 5. Agregar bancos.csv a partir de fontes locais

Se você possui múltiplos CSVs de ofertas de bancos (direto do site/app), coloque-os em:

```dados/fontes_bancos/*.csv```

Na UI, clique “Atualizar bancos.csv (agregar fontes locais)”. O agregador:

- Detecta encoding (utf-8, fallback latin1) e separador (,/;).
- Normaliza a modalidade → {SAC, SAC_TR, SAC_IPCA}.
- Converte taxa para fração anual (ex.: 11,5% → 0.115).
- Gera dados/bancos.csv com colunas nome, sistema, taxa_anual.
- Caso não encontre fontes válidas, cria um mínimo (fallback).
- Dica: se faltar taxa em alguma linha de origem, o agregador usa a taxa_base a.a. da UI como default (log informado).

---

### 6. Reproduzir as Evidências (passo a passo)

- Abrir a UI (ver §3).
- Se necessário, gerar bancos.csv via agregador (ver §5).
- Clicar “Executar comparação”.
- Confirmar no disco:
    - resultados/ranking.csv
    - resultados/graficos/ranking.png

---

### 7. Testes E2E (offline)

- Pré-condição: arquivos reais em dados/txjuros/ e um dados/bancos.csv válido.
- Rodar:
    ```bash
            $env:PYTHONPATH="src"
            pytest -q
    ```

- O teste E2E mínimo valida:
    - Ranking não vazio e com totais > 0.
    - Ordenação crescente por “Total Pago”.
    - Mensagem de recomendação não vazia.
    - Presença de ≥1 modalidade reconhecida no rótulo.

---

### 8. Estrutura de Pastas (essencial)

```
SAD-FI/
├─ src/
│  ├─ application/
│  │  └─ controlador.py
│  ├─ presentation/
│  │  ├─ ui_app.py
│  │  ├─ plots.py
│  │  ├─ bancos_aggregador.py
│  │  ├─ bancos_schema_fix.py
│  │  ├─ io_utils.py
│  │  └─ logging_setup.py
│  └─ ...
├─ dados/
│  ├─ bancos.csv
│  ├─ fontes_bancos/            # <— CSVs de origem (opcionais)
│  └─ txjuros/
│     ├─ IPCA_BACEN.csv
│     └─ TR_mensal_compat.csv
├─ resultados/
│  ├─ ranking.csv
│  └─ graficos/
│     └─ ranking.png
├─ tests/
│  └─ test_e2e_offline.py
└─ README.md
```
---

### 9. Solução de Problemas (Troubleshooting)

#### 9.1. ValueError: CSV inválido: faltam colunas obrigatórias: [...]

- Causa: dados/bancos.csv sem as colunas exigidas (ex.: nome, sistema, taxa_anual).
- Ação:
    1. Use o agregador (§4) para gerar bancos.csv válido; ou
    2. Ajuste manualmente o CSV para conter:

```csv
nome,sistema,taxa_anual
Banco A,SAC,0.11
Banco B,SAC_TR,0.11
Banco C,SAC_IPCA,0.11
```

- Observação: a UI possui autofix de schema e faz uma nova tentativa automaticamente ao detectar esse erro.

#### 9.2. Warnings de fonte: Glyph ... missing from font(s) DejaVu Sans
- Causa: caracteres C1 (mojibake) em rótulos/nome de instituição.
- Ação: o app normaliza textos (remoção de C0/C1, fix Latin-1/UTF-8). Se persistir, verifique os CSVs de origem e re-salve em UTF-8.

#### 9.3. ranking.png em branco
- Causa comum: salvar a figura depois de limpá-la.
- Correção: o app salva o PNG antes de exibir e sem clear_figure=True.

#### 9.4. Streamlit ocupado / encerrar
- Tente parar com Ctrl+C no terminal da UI.
- Se não responder, finalize o processo Python do Streamlit pelo Gerenciador de Tarefas.

---

### 10. Logs e Auditoria Rápida

- Ao abrir a UI, o terminal registra:

- Caminho, tamanho e mtime de cada arquivo selecionado.
    - Parâmetros da simulação (valor, entrada, prazo, taxa).
    - Resumo do ranking (menor/maior total e respectivas ofertas).
    - Caminhos absolutos dos artefatos salvos.
    - Avisos de fallback (template/mínimo; taxa default no agregador).

---

### 11. Roadmap pós-Sprint 
- Padronização de exportações CSV (ex.: utf-8-sig, sep=";").
- Execução headless do notebook (papermill/jupytext).
- Cache leve de séries (IPCA/TR) para acelerar execuções repetidas.
- Entrada alternativa com DataFrame no ControladorApp (fonte_ipca={"dataframe": df} etc.).

---

### 12. Créditos Técnicos

- UI: Streamlit + Matplotlib (plots legíveis, rótulos BRL, gradiente verde→vermelho).
- Normalização de texto: correção de mojibake (Latin-1/UTF-8), remoção de C0/C1.
- Agregador de bancos: merge de fontes locais com detecção de separador/encoding e schema compatível.


