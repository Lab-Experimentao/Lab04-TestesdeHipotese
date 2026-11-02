# Lab04-TestesdeHipotese

Testes de hipótese por dentro: cenário, simulação e visualização.

- **Dashboard:** <https://preencher-apos-publicar.streamlit.app>
- **GitHub Projects:** <https://github.com/users/lucasrsnd/projects/2>

## Como executar

Requer Python 3.10+. Instalação (uma vez, em ambiente virtual):

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

Comando único para abrir o dashboard:

```bash
streamlit run app.py
```

O dashboard abre em <http://localhost:8501>.

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
│   ├── raw/             # Dados reais coletados (~30 obs. por grupo)
│   └── processed/       # Resultados das simulações
└── src/
    └── config.py        # Semente, α, nº de simulações, paleta de cores e links
```

## Sugestão para os gráficos: Apache ECharts

Para G1–G4 (e o gráfico interativo do bônus), sugerimos o [Apache ECharts](https://echarts.apache.org/)
via [`streamlit-echarts`](https://pypi.org/project/streamlit-echarts/):

- visual mais refinado que o padrão do Plotly, com animações e tooltips prontos;
- `markArea` e `markLine` resolvem direto a região de rejeição sombreada (G2) e a linha de 5% (G3);
- `dataZoom` e eventos facilitam o bônus (variar n e o tamanho do efeito).

```bash
pip install streamlit-echarts
```

```python
from streamlit_echarts import st_echarts
from src.config import CORES_TESTES

st_echarts({
    "color": list(CORES_TESTES.values()),
    "xAxis": {"type": "value", "name": "Tamanho do efeito"},
    "yAxis": {"type": "value", "name": "Poder (proporção de rejeições)", "max": 1},
    "series": [{"name": nome, "type": "line", "data": [...]} for nome in CORES_TESTES],
}, height="420px")
```

## Reprodutibilidade

Toda aleatoriedade usa `src.config.get_rng()`, que cria `numpy.random.default_rng(42)`.
Cada teste tem uma cor fixa (`CORES_TESTES` em `src/config.py`), usada em todos os gráficos.
