
# SAD-FI – Sistema de Apoio à Decisão para Financiamento Imobiliário

Este é um projeto de MVP desenvolvido como trabalho final de pós-graduação em Ciência de Dados e Inteligência Artificial.  
O SAD-FI tem como objetivo auxiliar usuários leigos na simulação e comparação de modalidades de financiamento imobiliário.

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

```
SAD-FI/
├── dados/                  # Arquivos CSV com dados de entrada (ex.: IPCA)
├── notebooks/              # Notebooks Jupyter para orquestração e visualização
├── src/                    # Módulos Python com a lógica do domínio
├── resultados/             # Gráficos, tabelas e saídas geradas
├── requirements.txt        # Bibliotecas utilizadas
├── README.md               # Este arquivo
└── .gitignore              # Exclusões de versionamento
```

## 🚀 Como executar

1. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # ou venv\Scripts\activate no Windows
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute os notebooks desejados na pasta `notebooks/`.

## 🧪 Testes

Um notebook de testes (`testes_TDD.ipynb`) está disponível para conduzir o desenvolvimento com base em TDD (Test-Driven Development).

## 📄 Licença

Projeto acadêmico sem fins comerciais.
