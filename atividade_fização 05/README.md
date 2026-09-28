# Pipeline de Dados — Fintech

Projeto em Python para limpeza, transformação, consolidação, análise estatística e visualização de transações financeiras.

## Requisitos atendidos

- leitura de `transacoes.csv` com `encoding="latin1"`;
- imputação de `valor` pela mediana de cada estado;
- coluna estática `plataforma = "Mobile"`;
- `data_transacao` em datetime com `America/Sao_Paulo`;
- colunas de dia da semana e mês usando `.dt`;
- remoção de duplicatas mantendo a primeira ocorrência;
- filtro de setembro + (`SP` ou `RJ`) + valor acima de R$ 5.000 usando `&` e `|`;
- classificação de risco com `.map()`;
- `pivot_table` por mês e nível de risco, com `margins=True`;
- Z-Score por estado de forma vetorizada, sem `for`, e seleção de `Z > 2.5`;
- gráfico Matplotlib OO (`fig, ax = plt.subplots()`) com total diário e média móvel de 7 dias;
- consolidação opcional com `cotacoes.csv` pela data;
- dashboard em Streamlit.

## Estrutura

```text
fintech_pipeline/
├── app.py
├── pipeline.py
├── criar_dados.py
├── requirements.txt
├── .gitignore
├── dados/
└── saida/
```

## Como executar

### 1. Criar ambiente e instalar dependências

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Gerar os dados de teste

```bash
python criar_dados.py
```

O script cria `transacoes.csv` e `cotacoes.csv` na pasta atual.

### 3. Executar o pipeline

```bash
python pipeline.py
```

Os resultados ficam em `saida/`.

### 4. Abrir o dashboard

```bash
streamlit run app.py
```

No navegador, envie os CSVs gerados pelo script.

## Entrega no GitHub

Crie um repositório vazio no GitHub e, dentro desta pasta, execute:

```bash
git init
git add .
git commit -m "Projeto pipeline de dados fintech"
git branch -M main
git remote add origin URL_DO_SEU_REPOSITORIO
git push -u origin main
```

Substitua `URL_DO_SEU_REPOSITORIO` pela URL do repositório criado no GitHub.
