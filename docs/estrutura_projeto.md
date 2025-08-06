
# 📁 Estrutura de Diretórios – Projeto SAD-FI

O projeto está organizado segundo os princípios de **arquitetura em camadas** (Clean Architecture), com separação clara entre apresentação, aplicação, domínio e infraestrutura. Abaixo, detalha-se cada pasta e seu propósito.

---

## `src/` – Código-fonte principal

| Diretório                         | Camada               | Descrição                                                                 |
|----------------------------------|-----------------------|---------------------------------------------------------------------------|
| `presentation/`                  | Presentation Layer    | Responsável pela interação com o usuário: notebooks, CLI, futura GUI.     |
| `application/`                   | Application Layer     | Coordena o fluxo entre as camadas, executa casos de uso (ex: `ControladorApp`). |
| `domain/`                        | Domain Layer          | Contém as entidades e regras de negócio puras (ex: `Financiamento`, `SimuladorSAC`). |
| `infrastructure/data/`           | Infrastructure Layer  | Fornece acesso a dados externos, como leitura de CSVs (`TabelaIPCA`, `ler_csv`). |

---

## `tests/` – Testes automatizados

Contém scripts de teste por unidade, seguindo o padrão TDD.  
Cada arquivo testa uma classe ou módulo da camada de domínio ou infraestrutura.

Exemplos:
- `test_parcela.py`
- `test_simulador_sac.py`
- `test_tabela_ipca.py`

---

## `notebooks/` – Protótipos e análises

Inclui notebooks Jupyter utilizados para visualizações e validação dos simuladores.  
Exemplo:
- `01_visualizacao_simulacao.ipynb`

---

## `dados/` – Dados de entrada

Contém arquivos utilizados como fonte para simulações, como:
- `ipca.csv` (série histórica do IPCA)

---

## `resultados/` – Saídas do sistema

Organiza os outputs das simulações:
- `graficos/`: visualizações geradas
- Futuramente: `csv/`, `relatorios/`

---

## `docs/` – Documentação e diagramas UML

Inclui os diagramas do projeto (`*.puml`) e suas versões exportadas (`.png`), separados por tipo:

| Subpasta                     | Conteúdo                                         |
|-----------------------------|--------------------------------------------------|
| `docs/`                     | Arquivos-fonte (`camadas.puml`, `classes.puml`)  |
| `docs/out/`                 | Imagens exportadas para uso em relatórios        |
| `docs/out/camadas/`         | Diagrama de arquitetura                          |
| `docs/out/classes/`         | Diagrama de classes                              |
| `docs/out/estados/`         | Diagrama de estados                              |
| `docs/out/sequencia/`       | Diagrama de sequência                            |

---

## Arquivos diversos na raiz

| Arquivo                       | Finalidade                                        |
|------------------------------|---------------------------------------------------|
| `.gitignore`                 | Exclusão de arquivos desnecessários do Git       |
| `requirements.txt`          | Lista de bibliotecas Python do projeto           |
| `README.md`                 | Descrição geral do projeto                       |
| `cronograma_sprint1.md`     | Planejamento da Sprint 1                         |

---

### ✅ Considerações Finais

Essa organização favorece:

- Manutenção clara e modular
- Aplicação de TDD e versionamento estruturado
- Separação de responsabilidades segundo boas práticas
- Facilidade para expansão (ex: adicionar API, mais dados ou interface gráfica)
