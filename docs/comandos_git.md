# 📚 Comandos Git utilizados na Sprint 1

## 🔧 Configuração inicial do Git
```bash
git init                                  # Inicializa repositório local
git config --global user.name "Seu Nome"  # Define seu nome (se ainda não feito)
git config --global user.email "seu@email.com"  # Define seu e-mail
```

## 📦 Controle de versão dos arquivos
```bash
git status                                # Verifica status atual do repositório
git add nome_do_arquivo                   # Adiciona arquivo específico
git add .                                 # Adiciona todos os arquivos modificados
git commit -m "Mensagem descritiva"       # Salva o snapshot local com mensagem
```

## ⬆️ Envio para repositório remoto
```bash
git remote add origin https://github.com/usuario/repositorio.git  # Liga ao GitHub
git branch -M main                         # Define o nome da branch principal como "main"
git push -u origin main                    # Envia primeiro push (com rastreamento)
git push                                   # Envia commits futuros
```
## 🔁 Atualizações com versionamento contínuo
```bash
git add notebooks/01_visualizacao_simulacao.ipynb
git add src/financiamento.py src/parcela.py src/simulador_sac.py
git add tests/test_simulador_sac.py
git commit -m "📊 Refina visualizações SAC e estrutura da simulação"
git push
```
## 🗂️ Outras boas práticas utilizadas
```bash
pip freeze > requirements.txt             # Registra bibliotecas do ambiente virtual
echo venv/ > .gitignore                   # Impede o versionamento do venv
```
