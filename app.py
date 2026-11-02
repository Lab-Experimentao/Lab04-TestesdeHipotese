"""Dashboard do Lab04 - Testes de hipótese por dentro.

Execute com: streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.coleta import REPO
from src.config import (
    ALPHA,
    CORES_TESTES,
    DASHBOARD_URL,
    N_SIMULACOES,
    PROJECTS_URL,
    REPO_URL,
    SEED,
    TESTE_NAO_PARAMETRICO,
    TESTE_PARAMETRICO,
)
from src.descritiva import ARQUIVO_AMOSTRA, carregar_amostra, descritiva

CSS_PATH = Path(__file__).parent / "assets" / "style.css"
ELEGIVEIS_PATH = Path(__file__).parent / "data" / "raw" / "prs_elegiveis.csv"
NOMES_GRUPOS = {"sem_bot": "Sem bot", "com_bot": "Com bot"}

st.set_page_config(
    page_title="Lab04 - Testes de Hipótese",
    page_icon="📊",
    layout="wide",
)

# (âncora, título, gráfico, o que o texto deve dizer)
SECOES = [
    ("cenario", "Cenário", None,
     "A pergunta, H₀ e H₁, de onde vieram os dados reais e quantas observações foram coletadas."),
    ("dados", "Os dados", "G1",
     "Como são os dados reais e os simulados (assimetria, outliers) e por que os parâmetros "
     "da simulação foram escolhidos assim."),
    ("testes", "Como os testes funcionam", "G2",
     "O que cada teste compara, onde fica a região de rejeição e o que significa o p-valor do exemplo."),
    ("erro-tipo-1", "Erro tipo I", "G3",
     "Se cada teste ficou perto de 5% em cada situação, e qual se desviou."),
    ("poder", "Poder", "G4",
     "Qual teste detecta melhor o efeito, e em que situações a vantagem muda de lado."),
    ("dados-reais", "Dados reais", "Tabela",
     "Estatística, p-valor, tamanho do efeito e conclusão de cada teste nos dados coletados."),
    ("conclusao", "Conclusão", None,
     "O que o grupo esperava antes de simular × o que encontrou, e a recomendação."),
]


def aplicar_estilo() -> None:
    st.html(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>")


def cabecalho() -> None:
    legenda = "".join(
        f"<span class='key'><i style='background:{cor}'></i>{nome}</span>"
        for nome, cor in CORES_TESTES.items()
    )
    alpha = f"{ALPHA:.2f}".replace(".", ",")
    simulacoes = f"{N_SIMULACOES:,}".replace(",", ".")
    st.markdown(
        f"""
        <header class="top">
          <div class="top-bar">
            <span class="eyebrow">Laboratório 04 · Experimentação de Software</span>
            <nav class="links">
              <a href="{DASHBOARD_URL}" target="_blank">Dashboard ↗</a>
              <a href="{PROJECTS_URL}" target="_blank">GitHub Projects ↗</a>
              <a href="{REPO_URL}" target="_blank">Repositório ↗</a>
            </nav>
          </div>
          <h1>Testes de hipótese por dentro</h1>
          <p class="lede">Cenário, simulação e visualização: quando escolher um teste
          em vez de outro, medindo erro tipo I e poder em dados cuja resposta conhecemos.</p>
          <div class="meta">
            <span>α <b>{alpha}</b></span>
            <span><b>{simulacoes}</b> simulações</span>
            <span>semente <b>{SEED}</b></span>
            <span class="sep"></span>
            {legenda}
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def sidebar() -> None:
    itens = "".join(
        f"<a href='#{ancora}'><span>{i}</span>{titulo}</a>"
        for i, (ancora, titulo, _, _) in enumerate(SECOES, start=1)
    )
    st.sidebar.markdown(
        f"<div class='nav-title'>Seções</div><nav class='nav'>{itens}</nav>",
        unsafe_allow_html=True,
    )


@st.cache_data
def _dados_reais(versao: tuple[float, float]) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:  # noqa: ARG001
    amostra = carregar_amostra()
    elegiveis = pd.read_csv(ELEGIVEIS_PATH)
    return amostra, descritiva(amostra), elegiveis["grupo"].value_counts()


def dados_reais() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    # A data de modificação dos CSVs entra na chave do cache: uma nova coleta invalida o cache
    versao = (ARQUIVO_AMOSTRA.stat().st_mtime, ELEGIVEIS_PATH.stat().st_mtime)
    return _dados_reais(versao)


def fmt(x: float, casas: int = 1) -> str:
    """Número no formato brasileiro: 1.234,5"""
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def conteudo_cenario() -> None:
    welch = TESTE_PARAMETRICO
    mw = TESTE_NAO_PARAMETRICO
    amostra, _, elegiveis = dados_reais()
    n = amostra["grupo"].value_counts()
    st.markdown(
        f"""
        <p class="question">PRs revisados por um bot de revisão automática são mergeados
        em um tempo diferente dos PRs sem bot?</p>

        <div class="hyp">
          <div>
            <span class="hyp-label">H₀</span>
            <p>O tempo até o merge tem a mesma distribuição com e sem bot.</p>
            <ul class="hyp-tests">
              <li>{welch}: μ<sub>bot</sub> = μ<sub>sem</sub></li>
              <li>{mw}: P(X<sub>bot</sub> &gt; X<sub>sem</sub>) = ½</li>
            </ul>
          </div>
          <div>
            <span class="hyp-label">H₁</span>
            <p>O tempo até o merge é diferente com bot e sem bot.</p>
            <ul class="hyp-tests">
              <li>{welch}: μ<sub>bot</sub> ≠ μ<sub>sem</sub></li>
              <li>{mw}: P(X<sub>bot</sub> &gt; X<sub>sem</sub>) ≠ ½</li>
            </ul>
          </div>
        </div>

        <dl class="facts">
          <dt>Teste bicaudal</dt>
          <dd>O bot pode acelerar o merge (feedback imediato) ou atrasá-lo (mais comentários
          para resolver antes da aprovação). As duas direções interessam, e não temos razão
          prévia para descartar nenhuma.</dd>
          <dt>Expectativa antes de simular</dt>
          <dd>Esperamos que o <b>{mw}</b> se saia melhor. Tempos até o merge são muito
          assimétricos e têm outliers (PRs esquecidos por semanas), o que infla a variância e
          tira poder do {welch}, que compara médias. O {mw} compara postos e não é afetado
          pela magnitude dos valores extremos.</dd>
          <dt>Dados reais</dt>
          <dd>PRs mergeados do <a href="https://github.com/{REPO}" target="_blank">{REPO}</a>,
          coletados pela API do GitHub, antes e depois da adoção do bot de revisão CodeRabbit.
          <b>Sem bot:</b> {n["sem_bot"]} PRs sorteados entre {elegiveis["sem_bot"]} criados em
          out e nov/2024. <b>Com bot:</b> {n["com_bot"]} PRs sorteados entre
          {elegiveis["com_bot"]} criados em fev e mar/2025, todos revisados pelo bot.
          Dez/2024 e jan/2025, meses de transição, foram excluídos.</dd>
        </dl>
        """,
        unsafe_allow_html=True,
    )


def conteudo_dados() -> None:
    _, tabela, _ = dados_reais()
    linhas = [
        ("n", "n", 0),
        ("Média (h)", "media_h", 1),
        ("Mediana (h)", "mediana_h", 2),
        ("Desvio-padrão (h)", "desvio_h", 1),
        ("Mínimo – máximo (h)", None, 2),
        ("Assimetria", "assimetria", 2),
        ("Outliers (1,5 × IQR)", None, 0),
        ("Média do log", "media_log", 2),
        ("Desvio do log", "desvio_log", 2),
        ("Assimetria do log", "assimetria_log", 2),
    ]
    grupos = ["sem_bot", "com_bot"]
    corpo = ""
    for rotulo, coluna, casas in linhas:
        celulas = ""
        for g in grupos:
            r = tabela.loc[g]
            if rotulo.startswith("Mínimo"):
                valor = f"{fmt(r['min_h'], casas)} – {fmt(r['max_h'], casas)}"
            elif rotulo.startswith("Outliers"):
                valor = f"{int(r['outliers_n'])} ({fmt(r['outliers_pct'], 0)}%)"
            else:
                valor = fmt(r[coluna], casas)
            celulas += f"<td>{valor}</td>"
        corpo += f"<tr><th>{rotulo}</th>{celulas}</tr>"
    cabecalho_tabela = "".join(f"<th>{NOMES_GRUPOS[g]}</th>" for g in grupos)

    st.markdown(
        f"""
        <table class="stats-table">
          <thead><tr><th>Tempo até o merge</th>{cabecalho_tabela}</tr></thead>
          <tbody>{corpo}</tbody>
        </table>
        <div class="pending"><b>Pendente</b>G1: histograma dos dados reais ao lado dos
        simulados, e o texto sobre a escolha dos parâmetros da simulação.</div>
        """,
        unsafe_allow_html=True,
    )


# Seções já escritas; as demais mostram o aviso de pendente
CONTEUDOS = {
    "cenario": conteudo_cenario,
    "dados": conteudo_dados,
}


def secao(numero: int, ancora: str, titulo: str, grafico: str | None, descricao: str) -> None:
    tag = f"<span class='sec-tag'>{grafico}</span>" if grafico else ""
    st.markdown(
        f"<div class='sec-head' id='{ancora}'>"
        f"<span class='sec-num'>{numero}</span><h2>{titulo}</h2>{tag}</div>",
        unsafe_allow_html=True,
    )
    with st.container(key=f"sec-{ancora}"):
        if ancora in CONTEUDOS:
            CONTEUDOS[ancora]()
        else:
            st.markdown(
                f"<div class='pending'><b>Pendente</b>{descricao}</div>",
                unsafe_allow_html=True,
            )


aplicar_estilo()
cabecalho()
sidebar()
for i, s in enumerate(SECOES, start=1):
    secao(i, *s)
