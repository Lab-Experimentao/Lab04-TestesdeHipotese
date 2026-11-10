# Lab04-TestesdeHipotese

Testes de hipótese por dentro: cenário, simulação e visualização.

- **Dashboard:** <https://lab04-testes-hipotese.streamlit.app>
- **GitHub Projects:** <https://github.com/orgs/Lab-Experimentao/projects/3/views/1>

## Como executar

Requer Python 3.10+. Instalação (uma vez, em ambiente virtual):

```bash
python -m venv .venv
source .venv/bin/activate     # Linux/macOS
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Comando único para abrir o dashboard:

```bash
streamlit run app.py
```

O dashboard abre em <http://localhost:8501>.

**Bônus:** no fim da seção 5 (Poder), o bloco "Explore o poder" tem controles para o número de PRs
por grupo, o tamanho do efeito, a situação simulada e o α. O poder dos dois testes é recalculado na
hora (2.000 conjuntos por ponto), com as curvas de poder × efeito e poder × n e o n necessário para
80% de poder.

## Dados reais

Tempo até o merge de 30 PRs por grupo do [TryGhost/Ghost](https://github.com/TryGhost/Ghost),
antes e depois da adoção do bot de revisão CodeRabbit. Fonte e critérios em
[`data/raw/README.md`](data/raw/README.md). O CSV já está no repositório; para refazer a coleta
(requer `gh auth login`) e a análise descritiva:

```bash
python -m src.coleta       # gera data/raw/prs_elegiveis.csv e data/raw/prs_merge.csv
python -m src.descritiva   # gera data/processed/descritiva.csv
python -m src.testes       # gera data/processed/exemplo_simulado.csv
python -m src.monte_carlo  # gera data/processed/simulacoes.csv (10.000 repetições por configuração)
```

## Estrutura

```
.
├── app.py               # Dashboard Streamlit 
├── requirements.txt
├── assets/
│   └── style.css        # CSS próprio do dashboard (hero, cartões, navegação)
├── .streamlit/
│   └── config.toml      # Tema base do Streamlit
├── data/
│   ├── raw/             # Dados reais coletados (CSV + README com a fonte)
│   └── processed/       # Estatísticas descritivas e resultados das simulações
├── docs/
│   └── roteiro_apresentacao.md  # Perguntas da apresentação e onde mostrar cada resposta
└── src/
    ├── config.py        # Semente, α, nº de simulações, paleta de cores e links
    ├── coleta.py        # Coleta dos PRs pela API do GitHub
    ├── descritiva.py    # Média, mediana, assimetria e outliers por grupo
    ├── simulacao.py     # Gerador de dados simulados calibrado nos dados reais
    ├── monte_carlo.py   # Proporção de rejeições por situação × tamanho do efeito (Q1 a Q3)
    ├── testes.py        # t de Welch e Mann-Whitney: estatística, p-valor, efeito e distribuição sob H₀
    └── graficos.py      # Gráficos do dashboard, em Plotly (G1 a G4)
```

## Publicação

O dashboard está no [Streamlit Community Cloud](https://streamlit.io/cloud), ligado ao branch `main`
deste repositório (arquivo `app.py`, Python 3.12): cada push no `main` atualiza o app publicado.
Sem acessos por alguns dias, o app hiberna; ao abrir o link, basta clicar no botão para acordá-lo.

## Reprodutibilidade

Toda aleatoriedade usa `src.config.get_rng()`, que cria `numpy.random.default_rng(42)`.
Cada teste tem uma cor fixa (`CORES_TESTES` em `src/config.py`), usada em todos os gráficos.
