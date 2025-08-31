# SAD-FI – Sistema de Apoio à Decisão para Financiamento Imobiliário

Este é um projeto de MVP desenvolvido como trabalho final de pós-graduação em Ciência de Dados e Inteligência Artificial.  
O SAD-FI tem como objetivo auxiliar usuários leigos na simulação e comparação de modalidades de financiamento imobiliário.

## ✨ UI (offline) — Comparação SAC, SAC TR e SAC IPCA

Veja [`Como utilziar a UI`](docs/UI.md)

## Novidades da Sprint 3
- **Fluxo offline-first consolidado** com dados oficiais do Bacen via CSVs (IPCA e TR), eliminando dependência de rede nas evidências.

- **ControladorApp.simular_multiplos_bancos**: orquestra simulações em lote, gera ranking por custo total e mensagem de recomendação.

- **Comparador (multi)**: ranking estável (ordenação consistente em empates) e mensagem padronizada.

- **TR mensal compatível**: derivada da série diária (% → fração), agregação por mês e padding de lacunas.

- **TabelaIPCA / normalização**: carga via CSV oficial (latin-1, ;), conversão para fração e checagens de integridade.

- **Notebook 02 (evidências)**: consome a API do Controlador, produz resultados/ranking.csv e resultados/ranking.png (remoção de lógica duplicada — em andamento).

- **Reprodutibilidade**: ambiente congelado em requirements.txt, contratos claros de I/O e Diagrama de Contexto (Sprint 3) em PlantUML.

- **Leitor de bancos CSV**: validação de colunas, aceitação de vírgula decimal, normalização e deduplicação por menor taxa.

---

## 🎯 Objetivos

- Simular financiamentos com os sistemas SAC e SAC+IPCA
- Comparar modalidades com base em custo total e perfil do usuário
- Visualizar a evolução das parcelas e do saldo devedor
- Avaliar o impacto da antecipação de parcelas no financiamento

## 🧰 Tecnologias e Bibliotecas Utilizadas

- Python 3.x
- Pandas
- NumPy
- Matplotlib
- Scikit-learn (eventualmente)
- Jupyter Notebooks

## 📁 Estrutura do Projeto

A estrutura completa e detalhada do projeto, com explicações de cada pasta e camada da arquitetura, está documentada no arquivo [`estrutura_projeto.md`](docs/estrutura_projeto.md).

## 🧱 Arquitetura em Camadas

O projeto segue uma **arquitetura em camadas**:

1. **Presentation** – Interface com o usuário (wireframes/texto e notebook de visualização).
2. **Application** – `ControladorApp`, responsável por orquestrar as simulações, comparações, recomendações e exportações.
3. **Domain** – Regras de negócio e entidades (`Financiamento`, `Parcela`, `SimulacaoResultado`, simuladores SAC e SAC_IPCA, comparador, recomendador).
4. **Infrastructure / Data** – Acesso a dados (`TabelaIPCA`, `leitor_csv`, `salvar_ipca_tratado`) e função `exportar_cronograma_csv`.

## Diagramas (docs/out/)
Para manter rastreabilidade entre código e documentação, os principais diagramas estão disponíveis no diretório `docs/out/`:

| Tipo        | Arquivo                                                                                  | Descrição                                                                 |
|-------------|------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| Camadas     | [`Arquitetura Conceitual`](docs/out/docs/camadas/SADFI_Camadas_Sprint2_Simples_Clean.png) | Visão simples das camadas e suas relações.                                 |
| Classes     | [`Diagrama de Classes`](docs/out/docs/classes/classes_Sprint2_rev_parcela.png) | Classes atualizadas com TR opcional, vínculos corretos e atributos extras. |
| Estados     | [`Diagrama de Estados`](docs/out/docs/estados/SADFI_Estados_Sprint2_Linear.png)             | Fluxo linear e claro, com início e fim explícitos.                         |
| Sequência   | [`Diagrama de Sequência`](docs/out/docs/sequencia/SADFI_Sequencia_Sprint2_Rev_Fix.png)     | Fluxo de mensagens, com parâmetros de TR explícitos e exportação opcional. |
| Contexto    | [`Contexto Sprint 3`](docs/out/docs/contexto_sprint3/Contexto_SAD-FI_Sprint3.png)     | Visão do fluxo offline-first, fontes (CSVs Bacen), Controlador, Notebook e Testes. |

---


## ▶️ Como Executar o Projeto

1. Clone este repositório:
   ```bash
   git clone https://github.com/seu-usuario/sad-fi.git
   cd sad-fi
   ```

2. Crie o ambiente virtual:

   ```bash
   python -m venv venv
   ```

3. Ative o ambiente virtual:

   * **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   * **Linux/macOS**:
     ```bash
     source venv/bin/activate
     ```

4. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

5. Execute os notebooks disponíveis na pasta `notebooks/`.

---

## 🧪 Testes

Os testes são organizados na pasta tests/, com scripts dedicados para cada componente do sistema. O desenvolvimento segue abordagem TDD (Test-Driven Development), utilizando scripts simples com assert e print para facilitar a verificação manual. Futuramente, poderá ser adotado pytest para maior robustez e automação.

---

## 📄 Licença

Projeto acadêmico sem fins comerciais.

---

## 🗂️ Sprint 1 – Resumo das Issues

| #  | Título da Issue                                              | Etiqueta         | Status | Milestone |
|----|--------------------------------------------------------------|------------------|--------|-----------|
| 1  | Inicializar repositório com estrutura de pastas              | 🟩 Documentação   | ✅     | Sprint 1  |
| 2  | Configurar ambiente virtual e requirements.txt               | 🟩 Documentação   | ✅     | Sprint 1  |
| 3  | Implementar classe Financiamento                             | 🟦 Técnica        | ✅     | Sprint 1  |
| 4  | Implementar classe Parcela                                   | 🟦 Técnica        | ✅     | Sprint 1  |
| 5  | Implementar classe SimuladorSAC                              | 🟦 Técnica        | ✅     | Sprint 1  |
| 6  | Escrever testes para Financiamento, Parcela e SimuladorSAC  | 🟪 Testes         | ✅     | Sprint 1  |
| 7  | Gerar notebook de visualização da simulação SAC             | 🟨 Visualização   | ✅     | Sprint 1  |
| 8  | Refinar visualizações com foco em clareza e escala          | 🟨 Visualização   | ✅     | Sprint 1  |
| 9  | Versionar scripts, notebooks e arquivos auxiliares           | 🟩 Documentação   | ✅     | Sprint 1  |
| 10 | Criar planejamento e backlog de funcionalidades futuras      | 🟩 Documentação   |   ✅   | Sprint 1  |


---

## 🗂️ Sprint 2 – Resumo das Issues

| #  | Título da Issue                                              | Etiqueta         | Status | Milestone |
|----|--------------------------------------------------------------|------------------|--------|-----------|
| 11 | Implementar Simulador SAC com IPCA+                          | 🟦 Técnica        | ✅     | Sprint 2  |
| 12 | Implementar TR opcional no Simulador SAC                     | 🟦 Técnica        | ✅     | Sprint 2  |
| 13 | Criar função de comparação entre SAC fixo e SAC IPCA+        | 🟦 Técnica        | ✅     | Sprint 2  |
| 14 | Calcular e exibir custo total de cada modalidade             | 🟨 Visualização   | ✅     | Sprint 2  |
| 15 | Implementar regra simples de recomendação                    | 🟨 Visualização   | ✅     | Sprint 2  |
| 16 | Escrever testes para recomendação automática                 | 🟪 Testes         | ✅     | Sprint 2  |
| 17 | Escrever testes para função de exportação CSV                | 🟪 Testes         | ✅     | Sprint 2  |
| 18 | Escrever testes para ComparadorModalidades                   | 🟪 Testes         | ✅     | Sprint 2  |
| 19 | Escrever testes para SimuladorSAC_IPCA                        | 🟪 Testes         | ✅     | Sprint 2  |
| 20 | Escrever testes para SimuladorSAC com TR opcional             | 🟪 Testes         | ✅     | Sprint 2  |
| 21 | Escrever testes para TabelaIPCA                              | 🟪 Testes         | ✅     | Sprint 2  |
| 22 | Exportar cronograma da simulação em CSV                       | 🟦 Técnica        | ✅     | Sprint 2  |
| 23 | Coletar e validar dados históricos do IPCA                    | 🟩 Documentação   | ✅     | Sprint 2  |
| 24 | Criar esboço de interface gráfica para usuários leigos        | 🟩 Documentação   | ✅     | Sprint 2  |
| 25 | Documentar mudanças e extensões realizadas na Sprint 2        | 🟩 Documentação   | ✅     | Sprint 2  |
| 26 | Ajustar diagrama de classes para refletir TR e vínculos       | 🟩 Documentação   | ✅     | Sprint 2  |
| 27 | Revisar diagramas de estados e sequência                      | 🟩 Documentação   | ✅     | Sprint 2  |
| 28 | Atualizar README com entregas da Sprint 2                      | 🟩 Documentação   | ✅     | Sprint 2  |

---

|  # | Título da Issue                                                | Etiquetas                            | Prioridade | Status | Milestone |
| -: | -------------------------------------------------------------- | ------------------------------------ | ---------: | :----: | :-------: |
| 29 | task: **Docs, Diagramas e Evidências (finalização)**           | 🟩 Documentação                      |       must |    ⏳   |  Sprint 3 |
| 30 | task: **UI mínima / CLI (fallback)**                           | 🟩 Documentação, 🟨 Visualização     |     should |    ⭕   |  Sprint 3 |
| 31 | test: **Testes unitários e integração (Sprint 3)**             | 🟪 Testes                            |       must |    ✅   |  Sprint 3 |
| 32 | task: **Notebook — adaptar para consumir API do Controlador**  | 🟨 Visualização                      |       must |    ⏳   |  Sprint 3 |
| 33 | feat: **Controlador — simular\_multiplos\_bancos**             | 🟦 Técnica                           |       must |    ✅   |  Sprint 3 |
| 34 | feat: **Comparador (multi) — comparar\_varios + recomendar**   | 🟦 Técnica                           |       must |    ✅   |  Sprint 3 |
| 35 | feat: **Coletor BACEN 433 (stub + offline fixture)**           | 🟦 Técnica                           |     should |    ✅   |  Sprint 3 |
| 36 | feat: **TabelaIPCA.from\_dataframe(df)**                       | 🟦 Técnica                           |       must |    ✅   |  Sprint 3 |
| 37 | task: **Ambiente e dependências — atualizar requirements.txt** | 🟧 Reprodutibilidade & Empacotamento |       must |    ✅   |  Sprint 3 |
| 38 | test: **Leitor de bancos CSV — testes básicos**                | 🟪 Testes                            |       must |    ✅   |  Sprint 3 |
| 39 | feat: **Leitor de bancos CSV (carregar\_bancos\_csv)**         | 🟦 Técnica                           |       must |    ✅   |  Sprint 3 |



## 📚 Histórico de Comandos Git

A lista de comandos Git utilizados durante a Sprint 1 está disponível [neste arquivo separado](docs/comandos_git.md).



