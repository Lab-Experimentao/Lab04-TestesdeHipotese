"""Dashboard do Lab04 - Testes de hipótese por dentro.

Execute com: streamlit run app.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.coleta import REPO
from src.config import (
    ALPHA,
    CORES_TESTES,
    DASHBOARD_URL,
    N_SIMULACOES,
    NOMES_GRUPOS,
    PROJECTS_URL,
    REPO_URL,
    SEED,
    TESTE_NAO_PARAMETRICO,
    TESTE_PARAMETRICO,
    get_rng,
)
from src.descritiva import ARQUIVO_AMOSTRA, carregar_amostra, descritiva
from src.graficos import fmt, g1_real_simulado, g2_estatistica_h0
from src.simulacao import calibrar, gerar_conjunto
from src.testes import (
    EFEITO_EXEMPLO,
    N_EXEMPLO,
    SITUACAO_EXEMPLO,
    aplicar_testes,
    conjunto_exemplo,
    estatisticas_sob_h0,
    referencias_h0,
)

CSS_PATH = Path(__file__).parent / "assets" / "style.css"
ELEGIVEIS_PATH = Path(__file__).parent / "data" / "raw" / "prs_elegiveis.csv"
# Observações por grupo usadas para descrever a forma de cada gerador, sem o ruído de um conjunto só
N_REFERENCIA = 100_000
PERCENTIS = {"Mediana": 0.5, "P75": 0.75, "P90": 0.9, "P99": 0.99}

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


@st.cache_data
def _dados_simulados(versao: float, n: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:  # noqa: ARG001
    sem_bot, com_bot = gerar_conjunto(n, 0, "mistura", get_rng())
    conjunto = pd.DataFrame({
        "grupo": ["sem_bot"] * len(sem_bot) + ["com_bot"] * len(com_bot),
        "horas_ate_merge": np.concatenate([sem_bot, com_bot]),
    })
    elegiveis = pd.read_csv(ELEGIVEIS_PATH)["horas_ate_merge"]
    amostras = {
        "Elegíveis": elegiveis,
        "Mistura": pd.Series(np.concatenate(gerar_conjunto(N_REFERENCIA, 0, "mistura", get_rng()))),
        "Lognormal simples": pd.Series(
            np.concatenate(gerar_conjunto(N_REFERENCIA, 0, "lognormal", get_rng()))
        ),
    }
    quantis = pd.DataFrame({
        nome: x.quantile(list(PERCENTIS.values())).set_axis(list(PERCENTIS))
        for nome, x in amostras.items()
    })
    return conjunto, quantis, elegiveis


def dados_simulados(n: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    # Com efeito zero, as diferenças entre os dois grupos simulados são puro acaso
    return _dados_simulados(ELEGIVEIS_PATH.stat().st_mtime, n)


@st.cache_data
def _simulacao_h0(versao: float) -> dict[str, pd.DataFrame]:  # noqa: ARG001
    return estatisticas_sob_h0(N_EXEMPLO, SITUACAO_EXEMPLO, N_SIMULACOES, get_rng())


def simulacao_h0() -> dict[str, pd.DataFrame]:
    return _simulacao_h0(ELEGIVEIS_PATH.stat().st_mtime)


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


def intervalo(a: float, b: float, casas: int = 1) -> str:
    """Faixa entre dois valores, em ordem crescente; um valor só, se forem iguais no formato."""
    menor, maior = fmt(min(a, b), casas), fmt(max(a, b), casas)
    return menor if menor == maior else f"{menor} a {maior}"


def conteudo_dados() -> None:
    amostra, tabela, _ = dados_reais()
    n_grupo = int(tabela["n"].iloc[0])
    conjunto, quantis, elegiveis = dados_simulados(n_grupo)
    tabela_sim = descritiva(conjunto)
    c = calibrar()

    with st.container(key="grafico-g1"):
        st.plotly_chart(
            g1_real_simulado(amostra, conjunto),
            theme=None,
            config={"displayModeBar": False},
        )

    real_sem, real_com = tabela.loc["sem_bot"], tabela.loc["com_bot"]
    sim_sem, sim_com = tabela_sim.loc["sem_bot"], tabela_sim.loc["com_bot"]
    p90 = quantis.loc["P90"]
    st.markdown(
        f"""
        <dl class="facts">
          <dt>O que o gráfico mostra</dt>
          <dd>Cada linha é um grupo: à esquerda, os {n_grupo} PRs reais; à direita, {n_grupo} PRs
          de um conjunto simulado com efeito zero, em que os dois grupos vêm do mesmo gerador e
          as diferenças entre eles são puro acaso.</dd>
          <dt>Forma dos dados</dt>
          <dd>Reais e simulados são muito assimétricos e têm outliers: a mediana fica abaixo de
          1 h, a assimetria vai de {intervalo(real_sem["assimetria"], real_com["assimetria"])} nos
          reais e de {intervalo(sim_sem["assimetria"], sim_com["assimetria"])} nos simulados, e os
          outliers são {intervalo(real_sem["outliers_pct"], real_com["outliers_pct"], 0)}% dos
          reais e {intervalo(sim_sem["outliers_pct"], sim_com["outliers_pct"], 0)}% dos simulados.</dd>
          <dt>Parâmetros da simulação</dt>
          <dd>Usamos uma <b>mistura de duas lognormais</b>, ajustada por EM aos {len(elegiveis)}
          PRs elegíveis, porque o tempo até o merge tem dois picos (merges rápidos e lentos) e
          uma lognormal simples subestima a cauda: o P90 dela é de {fmt(p90["Lognormal simples"], 0)} h,
          contra {fmt(p90["Elegíveis"], 0)} h nos dados e {fmt(p90["Mistura"], 0)} h na mistura.</dd>
          <dt>Real × simulado</dt>
          <dd>Os conjuntos simulados têm mais PRs lentos do que os reais (média de
          {intervalo(sim_sem["media_h"], sim_com["media_h"])} h, contra
          {intervalo(real_sem["media_h"], real_com["media_h"])} h) porque a amostra real quase não
          pegou a cauda: seu máximo é de {fmt(max(real_sem["max_h"], real_com["max_h"]), 0)} h,
          contra {fmt(elegiveis.max(), 0)} h entre os elegíveis, de onde calibramos a simulação.</dd>
        </dl>
        """,
        unsafe_allow_html=True,
    )

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
    corpo = ""
    for rotulo, coluna, casas in linhas:
        celulas = ""
        for r in (real_sem, real_com, sim_sem, sim_com):
            if rotulo.startswith("Mínimo"):
                valor = f"{fmt(r['min_h'], casas)} – {fmt(r['max_h'], casas)}"
            elif rotulo.startswith("Outliers"):
                valor = f"{int(r['outliers_n'])} ({fmt(r['outliers_pct'], 0)}%)"
            else:
                valor = fmt(r[coluna], casas)
            celulas += f"<td>{valor}</td>"
        corpo += f"<tr><th>{rotulo}</th>{celulas}</tr>"
    nomes_grupos = "".join(f"<th>{nome}</th>" for nome in NOMES_GRUPOS.values()) * 2

    componentes = "".join(
        f"<tr><th>{nome}</th><td>{fmt(100 * peso, 0)}%</td>"
        f"<td>{fmt(np.exp(mu), 2)}</td><td>{fmt(sigma, 2)}</td></tr>"
        for nome, peso, mu, sigma in (
            ("Merges rápidos", 1 - c.peso_lento, c.mu_rapido, c.sigma_rapido),
            ("Merges lentos", c.peso_lento, c.mu_lento, c.sigma_lento),
        )
    )
    ajuste = "".join(
        f"<tr><th>{percentil}</th>" + "".join(f"<td>{fmt(v, 2 if v < 1 else 1)}</td>" for v in linha)
        + "</tr>"
        for percentil, linha in zip(quantis.index, quantis.to_numpy())
    )
    colunas_ajuste = "".join(f"<th>{nome}</th>" for nome in quantis.columns)

    st.markdown(
        f"""
        <div class="table-scroll">
          <table class="stats-table">
            <thead>
              <tr><th rowspan="2">Conjuntos do G1</th><th colspan="2">Reais</th><th colspan="2">Simulados</th></tr>
              <tr>{nomes_grupos}</tr>
            </thead>
            <tbody>{corpo}</tbody>
          </table>
        </div>
        <div class="tables-pair">
          <div class="table-scroll">
            <table class="stats-table">
              <caption>Parâmetros da mistura</caption>
              <thead><tr><th>Componente</th><th>Peso</th><th>Mediana (h)</th><th>Desvio do log</th></tr></thead>
              <tbody>{componentes}</tbody>
            </table>
          </div>
          <div class="table-scroll">
            <table class="stats-table">
              <caption>Ajuste aos {len(elegiveis)} elegíveis (h)</caption>
              <thead><tr><th>Percentil</th>{colunas_ajuste}</tr></thead>
              <tbody>{ajuste}</tbody>
            </table>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def conteudo_testes() -> None:
    welch = TESTE_PARAMETRICO
    mw = TESTE_NAO_PARAMETRICO
    sem_bot, com_bot = conjunto_exemplo()
    exemplo = aplicar_testes(sem_bot, com_bot)
    referencias = referencias_h0(sem_bot, com_bot)
    simulacoes = simulacao_h0()
    rejeicoes = {t: 100 * (s["p_valor"] < ALPHA).mean() for t, s in simulacoes.items()}
    t_critico = referencias[welch].limites_criticos[1]
    u_menor, u_maior = referencias[mw].limites_criticos
    multiplicador = np.exp(EFEITO_EXEMPLO * calibrar().sigma)

    with st.container(key="grafico-g2"):
        st.plotly_chart(
            g2_estatistica_h0(exemplo, referencias, simulacoes, ALPHA),
            theme=None,
            config={"displayModeBar": False},
        )

    st.markdown(
        f"""
        <dl class="facts">
          <dt>O que cada teste compara</dt>
          <dd>O <b>{welch}</b> compara as médias dos grupos, em erros-padrão; o <b>{mw}</b> compara
          os postos: o U conta em quantos dos {fmt(N_EXEMPLO ** 2, 0)} pares (com bot, sem bot) o PR
          com bot demorou mais, e cada empate vale meio.</dd>
          <dt>Região de rejeição</dt>
          <dd>Como o teste é bicaudal, α = {fmt(100 * ALPHA, 0)}% se divide entre as duas pontas da
          curva, onde ficam os valores que seriam raros se H₀ fosse verdadeira: |t| &gt;
          {fmt(t_critico, 2)} e U fora de {fmt(u_menor, 0)} a {fmt(u_maior, 0)}.</dd>
          <dt>P-valor do exemplo</dt>
          <dd>No exemplo, com {N_EXEMPLO} PRs por grupo e tempos com bot {fmt(multiplicador, 1)} vezes
          maiores, a área hachurada é a chance de um resultado tão ou mais extremo se H₀ fosse
          verdadeira, e não a probabilidade de H₀ ser verdadeira:
          {fmt(100 * exemplo.loc[welch, "p_valor"], 1)}% no {welch}, que não rejeita H₀ e comete um
          erro tipo II, e {fmt(100 * exemplo.loc[mw, "p_valor"], 1)}% no {mw}, que rejeita.</dd>
          <dt>Curva × simulação</dt>
          <dd>As barras mostram {fmt(N_SIMULACOES, 0)} conjuntos sem efeito: o U acompanha a curva,
          mas o t forma dois picos perto de ±1, porque o PR mais lento domina a média e a variância
          do próprio grupo, e só {fmt(rejeicoes[welch], 1)}% dos conjuntos rejeitam H₀ no {welch},
          contra {fmt(rejeicoes[mw], 1)}% no {mw}.</dd>
        </dl>
        """,
        unsafe_allow_html=True,
    )

    distribuicao_welch = referencias[welch].distribuicao
    linhas = {
        "Estatística no exemplo": (
            f"t = {fmt(exemplo.loc[welch, 'estatistica'], 2)}",
            f"U = {fmt(exemplo.loc[mw, 'estatistica'], 1)}",
        ),
        "Curva sob H₀": (
            f"t de Student, {fmt(distribuicao_welch.args[0], 1)} gl",
            f"Normal, média {fmt(referencias[mw].centro, 0)}, desvio {fmt(referencias[mw].distribuicao.std(), 1)}",
        ),
        "Região de rejeição": (
            f"|t| &gt; {fmt(t_critico, 2)}",
            f"U &lt; {fmt(u_menor, 0)} ou U &gt; {fmt(u_maior, 0)}",
        ),
        "P-valor": tuple(fmt(exemplo.loc[t, "p_valor"], 3) for t in (welch, mw)),
        f"Decisão a α = {fmt(ALPHA, 2)}": tuple(
            "Rejeita H₀" if exemplo.loc[t, "rejeita_h0"] else "Não rejeita H₀" for t in (welch, mw)
        ),
        "Tamanho do efeito": tuple(
            f"{exemplo.loc[t, 'medida_efeito']} = {fmt(exemplo.loc[t, 'efeito'], 2)}" for t in (welch, mw)
        ),
        "Rejeições sob H₀ (simulação)": tuple(f"{fmt(rejeicoes[t], 1)}%" for t in (welch, mw)),
    }
    corpo = "".join(
        f"<tr><th>{rotulo}</th><td>{a}</td><td>{b}</td></tr>" for rotulo, (a, b) in linhas.items()
    )
    st.markdown(
        f"""
        <div class="table-scroll">
          <table class="stats-table">
            <thead><tr><th>Conjunto de exemplo</th><th>{welch}</th><th>{mw}</th></tr></thead>
            <tbody>{corpo}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Seções já escritas; as demais mostram o aviso de pendente
CONTEUDOS = {
    "cenario": conteudo_cenario,
    "dados": conteudo_dados,
    "testes": conteudo_testes,
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
