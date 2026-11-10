"""Dashboard do Lab04 - Testes de hipótese por dentro.

Execute com: streamlit run app.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

from src.coleta import REPO
from src.config import (
    ALPHA,
    ALPHA_ESTRITO,
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
from src.graficos import (
    PODER_ALVO,
    fmt,
    g1_real_simulado,
    g2_estatistica_h0,
    g3_erro_tipo_1,
    g4_poder,
    poder_interativo as grafico_poder_interativo,
)
from src.monte_carlo import (
    ARQUIVO_SIMULACOES,
    EFEITOS_INTERATIVOS,
    FAIXA_ACEITAVEL,
    N_INTERATIVOS,
    N_SIMULACOES_INTERATIVO,
    Z_95,
    carregar_simulacoes,
    efeito_para_poder,
    erro_tipo_1,
    gerar_lote_da_configuracao,
    poder_interativo,
    valor_para_poder,
)
from src.simulacao import (
    LIMIAR_OUTLIER_H,
    N_PEQUENO,
    N_POR_GRUPO,
    PARCELA_MENOR,
    SITUACOES,
    calibrar,
    gerar_conjunto,
    gerar_lote,
)
from src.testes import (
    EFEITO_EXEMPLO,
    N_EXEMPLO,
    SITUACAO_EXEMPLO,
    aplicar_testes,
    conjunto_exemplo,
    erro_tipo_1_exato_mann_whitney,
    referencias_h0,
    testes_em_lote,
)

CSS_PATH = Path(__file__).parent / "assets" / "style.css"
ELEGIVEIS_PATH = Path(__file__).parent / "data" / "raw" / "prs_elegiveis.csv"
# Observações por grupo usadas para descrever a forma de cada gerador, sem o ruído de um conjunto só
N_REFERENCIA = 100_000
PERCENTIS = {"Mediana": 0.5, "P75": 0.75, "P90": 0.9, "P99": 0.99}
# Conjuntos usados para estimar a assimetria típica de cada situação
N_CONJUNTOS_ASSIMETRIA = 2_000
# Gráfico interativo: "Amostra pequena" é a mistura com n fixo, e ali o n já é um controle
SITUACOES_INTERATIVAS = [s for s in SITUACOES if s != "amostra_pequena"]
N_MIN_INTERATIVO, N_MAX_INTERATIVO = N_INTERATIVOS[0], N_INTERATIVOS[-1]

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
    # Os mesmos conjuntos do CSV: as taxas do G2 e do G3 são idênticas
    return testes_em_lote(*gerar_lote_da_configuracao(SITUACAO_EXEMPLO, 0))


def simulacao_h0() -> dict[str, pd.DataFrame]:
    return _simulacao_h0(ELEGIVEIS_PATH.stat().st_mtime)


@st.cache_data
def _simulacoes(versao: float) -> pd.DataFrame:  # noqa: ARG001
    return carregar_simulacoes()


def simulacoes() -> pd.DataFrame:
    versao = ARQUIVO_SIMULACOES.stat().st_mtime if ARQUIVO_SIMULACOES.exists() else 0.0
    return _simulacoes(versao)


@st.cache_data
def _assimetrias_tipicas(versao: float) -> dict[str, float]:  # noqa: ARG001
    assimetrias = {}
    for chave, situacao in SITUACOES.items():
        # Todos os conjuntos de uma vez: um a um, este cálculo dominava o primeiro carregamento
        lote = gerar_lote(N_CONJUNTOS_ASSIMETRIA, situacao.n, 0, chave, get_rng())
        assimetrias[chave] = float(np.median(np.concatenate([stats.skew(g, axis=1, bias=False) for g in lote])))
    return assimetrias


def assimetrias_tipicas() -> dict[str, float]:
    return _assimetrias_tipicas(ELEGIVEIS_PATH.stat().st_mtime)


@st.cache_data
def _testes_reais(versao: tuple[float, float]) -> dict[str, tuple[pd.DataFrame, int, int, float]]:  # noqa: ARG001
    """Por conjunto: resultados dos testes, PRs sem e com bot e deslocamento no log, em desvios."""
    conjuntos = {"Amostra": carregar_amostra(), "Elegíveis": pd.read_csv(ELEGIVEIS_PATH)}
    resultados = {}
    for nome, df in conjuntos.items():
        sem_bot, com_bot = (df.loc[df["grupo"] == g, "horas_ate_merge"].to_numpy() for g in NOMES_GRUPOS)
        # Mesma unidade do efeito simulado, para ler o poder no G4
        deslocamento = (np.log(com_bot).mean() - np.log(sem_bot).mean()) / calibrar().sigma
        resultados[nome] = (aplicar_testes(sem_bot, com_bot), len(sem_bot), len(com_bot), float(deslocamento))
    return resultados


def testes_reais() -> dict[str, tuple[pd.DataFrame, int, int, float]]:
    return _testes_reais((ARQUIVO_AMOSTRA.stat().st_mtime, ELEGIVEIS_PATH.stat().st_mtime))


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
          <dd>À esquerda, os {n_grupo} PRs reais de cada grupo; à direita, {n_grupo} PRs simulados
          com efeito zero, em que as diferenças entre os grupos são puro acaso.</dd>
          <dt>Forma dos dados</dt>
          <dd>Os dois são muito assimétricos, com mediana abaixo de 1 h: a assimetria vai de
          {intervalo(real_sem["assimetria"], real_com["assimetria"])} nos reais e de
          {intervalo(sim_sem["assimetria"], sim_com["assimetria"])} nos simulados, e os outliers são
          {intervalo(real_sem["outliers_pct"], real_com["outliers_pct"], 0)}% e
          {intervalo(sim_sem["outliers_pct"], sim_com["outliers_pct"], 0)}% dos PRs.</dd>
          <dt>Parâmetros da simulação</dt>
          <dd>Simulamos uma <b>mistura de duas lognormais</b> ajustada aos {len(elegiveis)} PRs
          elegíveis, porque o tempo tem dois picos (merges rápidos e lentos) e a lognormal simples
          subestima a cauda: P90 de {fmt(p90["Lognormal simples"], 0)} h, contra
          {fmt(p90["Elegíveis"], 0)} h nos dados e {fmt(p90["Mistura"], 0)} h na mistura.</dd>
          <dt>Real × simulado</dt>
          <dd>Os simulados têm mais PRs lentos (média de {intervalo(sim_sem["media_h"], sim_com["media_h"])} h,
          contra {intervalo(real_sem["media_h"], real_com["media_h"])} h) porque a amostra real quase não
          pegou a cauda: seu máximo é de {fmt(max(real_sem["max_h"], real_com["max_h"]), 0)} h, contra
          {fmt(elegiveis.max(), 0)} h entre os elegíveis.</dd>
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
    tabela_situacoes(c)


def tabela_situacoes(c) -> None:
    assimetrias = assimetrias_tipicas()
    menor = round(2 * SITUACOES["desbalanceado"].n * PARCELA_MENOR)
    tamanhos = {"desbalanceado": f"{menor} e {2 * SITUACOES['desbalanceado'].n - menor}"}
    corpo = "".join(
        f"<tr><th>{s.nome}</th><td class='num'>{tamanhos.get(chave, s.n)}</td>"
        f"<td class='num'>{fmt(assimetrias[chave], 1)}</td>"
        f"<td>{s.descricao}</td><td>{s.pressuposto}</td><td>{s.justificativa}</td></tr>"
        for chave, s in SITUACOES.items()
    )
    dias = LIMIAR_OUTLIER_H // 24
    st.markdown(
        f"""
        <div class="table-scroll">
          <table class="stats-table situations-table">
            <caption>Situações da simulação (Q1 a Q3)</caption>
            <thead><tr><th>Situação</th><th class="num">PRs por grupo</th><th class="num">Assimetria típica</th>
            <th>Como é gerada</th><th>O que viola no Welch</th><th>Por que simular</th></tr></thead>
            <tbody>{corpo}</tbody>
          </table>
        </div>
        <p class="table-note">Em todas, o tamanho do efeito é um deslocamento no log dos tempos, em
        desvios ({fmt(c.sigma, 2)}), para que os resultados sejam comparáveis. Em "Outliers",
        {fmt(100 * c.parcela_outlier, 1)}% dos PRs (a parcela real parada por mais de {dias} dias) são
        deslocados em {fmt(c.deslocamento_outlier, 1)} desvios (a distância do PR real mais lento até
        a mediana).</p>
        """,
        unsafe_allow_html=True,
    )


def conteudo_testes() -> None:
    welch = TESTE_PARAMETRICO
    mw = TESTE_NAO_PARAMETRICO
    sem_bot, com_bot = conjunto_exemplo()
    exemplo = aplicar_testes(sem_bot, com_bot)
    referencias = referencias_h0(sem_bot, com_bot)
    estatisticas_h0 = simulacao_h0()
    rejeicoes = {t: 100 * (s["p_valor"] < ALPHA).mean() for t, s in estatisticas_h0.items()}
    t_critico = referencias[welch].limites_criticos[1]
    u_menor, u_maior = referencias[mw].limites_criticos
    multiplicador = np.exp(EFEITO_EXEMPLO * calibrar().sigma)

    with st.container(key="grafico-g2"):
        st.plotly_chart(
            g2_estatistica_h0(exemplo, referencias, estatisticas_h0, ALPHA),
            theme=None,
            config={"displayModeBar": False},
        )

    st.markdown(
        f"""
        <dl class="facts">
          <dt>O que cada teste compara</dt>
          <dd>O <b>{welch}</b> compara as médias dos grupos, em erros-padrão; o <b>{mw}</b> conta em
          quantos dos {fmt(N_EXEMPLO ** 2, 0)} pares (com bot, sem bot) o PR com bot demorou mais (U),
          e cada empate vale meio.</dd>
          <dt>Região de rejeição</dt>
          <dd>Como o teste é bicaudal, os {fmt(100 * ALPHA, 0)}% de α se dividem entre as duas pontas
          da curva: rejeita-se H₀ se |t| &gt; {fmt(t_critico, 2)} ou se U ficar fora de
          {fmt(u_menor, 0)} a {fmt(u_maior, 0)}.</dd>
          <dt>P-valor do exemplo</dt>
          <dd>Com tempos {fmt(multiplicador, 1)} vezes maiores com bot, a área hachurada (a chance de um
          resultado tão extremo se H₀ fosse verdadeira, não a de H₀ ser verdadeira) é de
          {fmt(100 * exemplo.loc[welch, "p_valor"], 1)}% no {welch}, que comete um erro tipo II, e de
          {fmt(100 * exemplo.loc[mw, "p_valor"], 1)}% no {mw}, que rejeita H₀.</dd>
          <dt>Curva × simulação</dt>
          <dd>Nos {fmt(N_SIMULACOES, 0)} conjuntos sem efeito (barras), o U segue a curva, mas o t forma
          dois picos perto de ±1, porque o PR mais lento domina a média e a variância do grupo, e só
          {fmt(rejeicoes[welch], 1)}% rejeitam H₀ no {welch}, contra {fmt(rejeicoes[mw], 1)}% no {mw}.</dd>
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


def conteudo_erro_tipo_1() -> None:
    welch = TESTE_PARAMETRICO
    mw = TESTE_NAO_PARAMETRICO
    erro = erro_tipo_1(simulacoes(), ALPHA).set_index(["situacao", "teste"])
    erro_estrito = erro_tipo_1(simulacoes(), ALPHA_ESTRITO).set_index(["situacao", "teste"])

    with st.container(key="grafico-g3"):
        st.plotly_chart(
            g3_erro_tipo_1(erro.reset_index(), ALPHA),
            theme=None,
            config={"displayModeBar": False},
        )

    def taxa(situacao: str, teste: str = welch) -> str:
        return f"{fmt(100 * erro.loc[(situacao, teste), 'proporcao'], 1)}%"

    taxas_mw = erro.xs(mw, level="teste")["proporcao"]
    desigual = erro.loc[("desbalanceado", welch)]
    exato_30 = erro_tipo_1_exato_mann_whitney(N_POR_GRUPO, N_POR_GRUPO)
    exato_10 = erro_tipo_1_exato_mann_whitney(N_PEQUENO, N_PEQUENO)
    faixa = [100 * ALPHA * limite for limite in FAIXA_ACEITAVEL]

    st.markdown(
        f"""
        <dl class="facts">
          <dt>O que o gráfico mostra</dt>
          <dd>Cada ponto é a proporção de p &lt; {fmt(ALPHA, 2)} em {fmt(N_SIMULACOES, 0)} conjuntos
          sem efeito, com margem de erro de 95%: como H₀ é verdadeira, toda rejeição é erro tipo I, e
          o esperado é ficar perto de {fmt(100 * ALPHA, 0)}%.</dd>
          <dt>{mw}</dt>
          <dd>Ficou perto de {fmt(100 * ALPHA, 0)}% em todas as situações
          ({fmt(100 * taxas_mw.min(), 1)}% a {fmt(100 * taxas_mw.max(), 1)}%), porque, sob H₀, os postos
          têm a mesma distribuição qualquer que seja a forma dos dados.</dd>
          <dt>{welch}</dt>
          <dd>Ficou perto de {fmt(100 * ALPHA, 0)}% no controle ({taxa("normal")}) e com outliers
          ({taxa("outliers")}), mas foi <b>conservador</b> com assimetria forte ({taxa("mistura")} no
          cenário principal, {taxa("lognormal")} na lognormal e {taxa("amostra_pequena")} com amostra
          pequena), porque um PR muito lento infla o desvio do próprio grupo.</dd>
          <dt>Grupos desiguais</dt>
          <dd>Os {taxa("desbalanceado")} do {welch} escondem outro desvio:
          {int(desigual["rejeicoes_com_bot_maior"])} das {int(desigual["rejeicoes"])} rejeições apontam
          merge mais lento com bot, em vez de se dividirem entre os lados, porque ocorrem quando o
          grupo menor fica sem PRs lentos.</dd>
        </dl>
        """,
        unsafe_allow_html=True,
    )

    def celula_taxa(linha: pd.Series) -> str:
        if not linha["h0_verdadeira"]:
            return "–"
        return f"{fmt(100 * linha['proporcao'], 2)}% ± {fmt(100 * linha['margem_erro'], 2)}"

    corpo = ""
    for chave, situacao in SITUACOES.items():
        l_welch, l_mw = erro.loc[(chave, welch)], erro.loc[(chave, mw)]
        corpo += (
            f"<tr><th>{situacao.nome}</th>"
            f"<td class='num'>{celula_taxa(l_welch)}</td><td>{l_welch['diagnostico']}</td>"
            f"<td class='num'>{celula_taxa(l_mw)}</td><td>{l_mw['diagnostico']}</td>"
            f"<td class='num'>{celula_taxa(erro_estrito.loc[(chave, welch)])}</td>"
            f"<td class='num'>{celula_taxa(erro_estrito.loc[(chave, mw)])}</td></tr>"
        )
    variancias = erro.loc[("variancias_diferentes", welch)]
    st.markdown(
        f"""
        <div class="table-scroll">
          <table class="stats-table situations-table">
            <caption>Erro tipo I por situação</caption>
            <thead><tr><th>Situação</th><th class="num">{welch}</th><th>Diagnóstico</th>
            <th class="num">{mw}</th><th>Diagnóstico</th>
            <th class="num">{welch} (α = {fmt(ALPHA_ESTRITO, 2)})</th>
            <th class="num">{mw} (α = {fmt(ALPHA_ESTRITO, 2)})</th></tr></thead>
            <tbody>{corpo}</tbody>
          </table>
        </div>
        <p class="table-note">"Perto" é a faixa de {fmt(faixa[0], 1)}% a {fmt(faixa[1], 1)}%, o critério
        liberal de Bradley (1978). Conservador é o teste que rejeita menos que α: ele erra menos do que
        promete, mas o custo aparece no poder (seção 5). O {mw} tende a ficar um pouco abaixo de α por
        causa da correção de continuidade: sem empates, a taxa exata é de {fmt(100 * exato_30, 1)}% com
        {N_POR_GRUPO} PRs por grupo e de {fmt(100 * exato_10, 1)}% com {N_PEQUENO}. Em "Variâncias
        diferentes", com efeito zero, as médias dos grupos diferem: a H₀ do {welch} é falsa, e seus
        {fmt(100 * variancias["proporcao"], 1)}% não são erro tipo I.</p>
        """,
        unsafe_allow_html=True,
    )


def curvas_poder() -> pd.DataFrame:
    """Proporção de rejeições a α = ALPHA, indexada por situação, teste e efeito."""
    sim = simulacoes()
    return sim[sim["alpha"] == ALPHA].set_index(["situacao", "teste", "efeito"])


def poder(situacao: str, teste: str, efeito: float = EFEITO_EXEMPLO) -> float:
    return curvas_poder().loc[(situacao, teste, efeito), "proporcao"]


def efeitos_simulados() -> list[float]:
    return sorted(curvas_poder().index.get_level_values("efeito").unique())


def vantagem_welch(situacao: str) -> pd.Series:
    """Poder do Welch menos o do Mann-Whitney, por efeito, sem o efeito zero."""
    return pd.Series({
        e: poder(situacao, TESTE_PARAMETRICO, e) - poder(situacao, TESTE_NAO_PARAMETRICO, e)
        for e in efeitos_simulados()
        if e > 0
    })


def vantagem_welch_no_controle() -> tuple[float, float, bool]:
    """Maior vantagem do Welch no controle normal, o efeito em que ocorre e se supera a margem de erro."""
    vantagem = vantagem_welch("normal")
    efeito = vantagem.idxmax()
    margem = np.hypot(*(
        curvas_poder().loc[("normal", t, efeito), "margem_erro"] for t in (TESTE_PARAMETRICO, TESTE_NAO_PARAMETRICO)
    ))
    return float(vantagem.max()), float(efeito), bool(vantagem.max() > margem)


def efeito_real() -> float:
    """Deslocamento observado nos elegíveis, em módulo, na unidade do efeito simulado."""
    return abs(testes_reais()["Elegíveis"][3])


def poder_no_efeito_real(teste: str) -> float:
    efeitos = efeitos_simulados()
    return float(np.interp(efeito_real(), efeitos, [poder(SITUACAO_EXEMPLO, teste, e) for e in efeitos]))


def conteudo_poder() -> None:
    welch = TESTE_PARAMETRICO
    mw = TESTE_NAO_PARAMETRICO
    sim = simulacoes()
    sim = sim[sim["alpha"] == ALPHA]

    with st.container(key="grafico-g4"):
        st.plotly_chart(g4_poder(sim, ALPHA, efeito_real()), theme=None, config={"displayModeBar": False})

    curvas = curvas_poder()
    efeitos = efeitos_simulados()
    vantagem_normal, _, welch_ganha = vantagem_welch_no_controle()
    outliers = vantagem_welch("outliers")
    maximo_welch = sim[(sim["situacao"] == SITUACAO_EXEMPLO) & (sim["teste"] == welch)]["proporcao"].max()
    multiplicador = np.exp(EFEITO_EXEMPLO * calibrar().sigma)

    st.markdown(
        f"""
        <dl class="facts">
          <dt>O que o gráfico mostra</dt>
          <dd>Cada ponto é a proporção de {fmt(N_SIMULACOES, 0)} conjuntos com p &lt; {fmt(ALPHA, 2)}
          quando o efeito existe (no efeito zero, é o erro tipo I da seção 4), e a linha tracejada
          marca {fmt(100 * PODER_ALVO, 0)}%, o poder usual de referência.</dd>
          <dt>Quem detecta melhor</dt>
          <dd>O <b>{mw}</b>, em todas as violações: no cenário principal, com tempos
          {fmt(multiplicador, 1)} vezes maiores com bot, ele detecta o efeito em
          {fmt(100 * poder(SITUACAO_EXEMPLO, mw), 0)}% dos conjuntos, contra
          {fmt(100 * poder(SITUACAO_EXEMPLO, welch), 0)}% do {welch}, que não passa de
          {fmt(100 * maximo_welch, 0)}% nem com o maior efeito.</dd>
          <dt>Onde a vantagem muda de lado</dt>
          <dd>Só no controle normal, em que os pressupostos do {welch} valem, ele supera o {mw}, por até
          {fmt(100 * vantagem_normal, 1)} pontos ({"acima" if welch_ganha else "dentro"} da margem de erro);
          com outliers, o {mw} ainda ganha, mas por no máximo {fmt(-100 * outliers.min(), 1)} pontos.</dd>
          <dt>E nos dados reais</dt>
          <dd>No efeito observado nos elegíveis ({fmt(efeito_real(), 2)}, linha pontilhada), as curvas
          mal saem do chão: com {N_POR_GRUPO} PRs por grupo, o poder é de
          {fmt(100 * poder_no_efeito_real(mw), 0)}% no {mw} e {fmt(100 * poder_no_efeito_real(welch), 0)}%
          no {welch}.</dd>
        </dl>
        """,
        unsafe_allow_html=True,
    )

    def celula_efeito(situacao: str, teste: str) -> str:
        curva = sim[(sim["situacao"] == situacao) & (sim["teste"] == teste)]
        efeito = efeito_para_poder(curva, PODER_ALVO)
        if efeito is None:
            return f"<span class='txt'>Não chega (máx. {fmt(100 * curva['proporcao'].max(), 0)}%)</span>"
        return f"{fmt(efeito, 2)} <span class='unit'>× {fmt(np.exp(efeito * calibrar().sigma), 1)}</span>"

    def tabela(titulo: str, celula) -> str:
        corpo = "".join(
            f"<tr><th>{s.nome}</th>" + "".join(f"<td>{celula(chave, t)}</td>" for t in (welch, mw)) + "</tr>"
            for chave, s in SITUACOES.items()
        )
        return (
            f"<div class='table-scroll'><table class='stats-table result-table'><caption>{titulo}</caption>"
            f"<thead><tr><th>Situação</th><th>{welch}</th><th>{mw}</th></tr></thead><tbody>{corpo}</tbody></table></div>"
        )

    def celula_poder(situacao: str, teste: str) -> str:
        linha = curvas.loc[(situacao, teste, EFEITO_EXEMPLO)]
        return f"{fmt(100 * linha['proporcao'], 1)}% <span class='unit'>± {fmt(100 * linha['margem_erro'], 1)}</span>"

    st.markdown(
        f"""
        <div class="tables-pair">
          {tabela(f"Poder com efeito {fmt(EFEITO_EXEMPLO, 1)} (tempos × {fmt(multiplicador, 1)})", celula_poder)}
          {tabela(f"Efeito necessário para {fmt(100 * PODER_ALVO, 0)}% de poder", celula_efeito)}
        </div>
        <p class="table-note">O efeito é o deslocamento do grupo com bot no log dos tempos, em desvios;
        o multiplicador ao lado é quantas vezes os tempos crescem. O efeito para {fmt(100 * PODER_ALVO, 0)}%
        é interpolado entre os {len(efeitos)} efeitos simulados, e a margem é de 95%. Em "Amostra pequena",
        são {N_PEQUENO} PRs por grupo; nas demais, {N_POR_GRUPO}.</p>
        """,
        unsafe_allow_html=True,
    )
    explorar_poder()


@st.cache_data(max_entries=5_000, show_spinner=False)
def _poder_ponto(versao: float, situacao: str, n: int, efeito: float) -> pd.DataFrame:  # noqa: ARG001
    return poder_interativo(situacao, n, efeito)


def poder_ponto(situacao: str, n: int, efeito: float) -> pd.DataFrame:
    # Arredondar evita entradas duplicadas no cache por ruído de ponto flutuante do slider
    return _poder_ponto(ELEGIVEIS_PATH.stat().st_mtime, situacao, n, round(efeito, 3))


def curvas_interativas(situacao: str, n: int, efeito: float, alpha: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Poder × efeito no n escolhido e poder × n no efeito escolhido, com o ponto escolhido incluído."""
    efeitos = sorted(set(EFEITOS_INTERATIVOS) | {round(efeito, 3)})
    tamanhos = sorted(set(N_INTERATIVOS) | {n})
    por_efeito = pd.concat([poder_ponto(situacao, n, e) for e in efeitos], ignore_index=True)
    por_n = pd.concat([poder_ponto(situacao, v, efeito) for v in tamanhos], ignore_index=True)
    return por_efeito[por_efeito["alpha"] == alpha], por_n[por_n["alpha"] == alpha]


def vezes(multiplicador: float) -> str:
    return fmt(multiplicador, 2 if multiplicador < 2 else 1 if multiplicador < 10 else 0)


def chance_em_coletas(p: float) -> str:
    """Poder em linguagem de coletas: "em cerca de 3 de cada 10 coletas (35%)"."""
    pct = f"{fmt(100 * p, 1 if p < 0.1 else 0)}%"
    if p == 0:
        return f"em nenhuma das {fmt(N_SIMULACOES_INTERATIVO, 0)} coletas simuladas"
    if p < 0.15:
        return f"{'quase nunca' if p < 0.02 else 'raramente'} ({pct}, cerca de 1 a cada {fmt(round(1 / p), 0)} coletas)"
    if p < 0.95:
        return f"em cerca de {round(10 * p)} de cada 10 coletas ({pct})"
    return f"quase sempre ({pct})"


def _usar_dados_reais() -> None:
    st.session_state["interativo_n"] = N_POR_GRUPO
    st.session_state["interativo_efeito"] = round(efeito_real(), 2)


@st.fragment
def explorar_poder() -> None:
    """Bônus: o poder dos dois testes recalculado para o n e o efeito escolhidos nos controles."""
    welch = TESTE_PARAMETRICO
    mw = TESTE_NAO_PARAMETRICO
    st.markdown(
        """
        <div class="subhead"><h3>Explore o poder</h3><span class="sec-tag">Bônus</span></div>
        <p class="table-note">Mude o tamanho da amostra e o tamanho do efeito para ver o poder dos dois
        testes mudar. Cada ponto é recalculado na hora, a partir do mesmo gerador do G4.</p>
        """,
        unsafe_allow_html=True,
    )

    # Valores iniciais pelo session_state, que o botão "Usar os dados reais" também altera
    st.session_state.setdefault("interativo_n", N_POR_GRUPO)
    st.session_state.setdefault("interativo_efeito", float(EFEITO_EXEMPLO))

    col_n, col_efeito, col_situacao, col_alpha = st.columns([1.2, 1.2, 1.2, 0.8], gap="medium")
    n = col_n.slider(
        "PRs por grupo (n)",
        N_MIN_INTERATIVO,
        N_MAX_INTERATIVO,
        step=5,
        key="interativo_n",
    )
    efeito = col_efeito.slider(
        "Tamanho do efeito (desvios no log)",
        0.0,
        float(max(EFEITOS_INTERATIVOS)),
        step=0.01,
        key="interativo_efeito",
        help="Deslocamento do grupo com bot no log dos tempos. Zero é H₀ verdadeira.",
    )
    situacao = col_situacao.selectbox(
        "Situação simulada",
        SITUACOES_INTERATIVAS,
        index=SITUACOES_INTERATIVAS.index(SITUACAO_EXEMPLO),
        format_func=lambda s: SITUACOES[s].nome,
        key="interativo_situacao",
    )
    alpha = col_alpha.radio(
        "Nível α",
        [ALPHA, ALPHA_ESTRITO],
        format_func=lambda a: fmt(a, 2),
        horizontal=True,
        key="interativo_alpha",
    )
    st.button(
        f"Usar os dados reais (n = {N_POR_GRUPO}, efeito = {fmt(efeito_real(), 2)})",
        on_click=_usar_dados_reais,
        type="tertiary",
    )

    with st.spinner("Simulando..."):
        por_efeito, por_n = curvas_interativas(situacao, n, efeito, alpha)
    multiplicador = float(np.exp(efeito * calibrar().sigma))
    ponto = por_efeito[np.isclose(por_efeito["efeito"], round(efeito, 3))].set_index("teste")

    def cartao(teste: str) -> str:
        linha = ponto.loc[teste]
        if efeito == 0:
            o_que = "de alarmes falsos"
            alvo = "Sem efeito, não há o que detectar"
        else:
            o_que = "de chance de detectar o efeito"
            valor = valor_para_poder(por_n[por_n["teste"] == teste], PODER_ALVO, "n")
            if valor is None:
                alvo = f"Não chega a {fmt(100 * PODER_ALVO, 0)}% nem com {N_MAX_INTERATIVO} PRs por grupo"
            elif linha["proporcao"] >= PODER_ALVO:
                alvo = (
                    f"Já passa de {fmt(100 * PODER_ALVO, 0)}%, o padrão em pesquisa: "
                    f"bastariam ~{fmt(np.ceil(valor), 0)} PRs por grupo"
                )
            else:
                alvo = (
                    f"Para chegar a {fmt(100 * PODER_ALVO, 0)}%, o padrão em pesquisa: "
                    f"~{fmt(np.ceil(valor), 0)} PRs por grupo"
                )
        return (
            f"<div><span class='key'><i style='background:{CORES_TESTES[teste]}'></i>{teste}</span>"
            f"<b>{fmt(100 * linha['proporcao'], 1)}%</b>"
            f"<small>{o_que} (± {fmt(100 * linha['margem_erro'], 1)})</small><small>{alvo}</small></div>"
        )

    cartoes = cartao(welch) + cartao(mw)
    diferenca = ponto.loc[mw, "proporcao"] - ponto.loc[welch, "proporcao"]
    margem = np.hypot(ponto.loc[welch, "margem_erro"], ponto.loc[mw, "margem_erro"])
    if abs(diferenca) <= margem:
        veredito = "Empate, dentro da margem de erro"
    else:
        veredito = f"{mw if diferenca > 0 else welch} à frente"
    if efeito == 0:
        leitura = (
            f"Com efeito zero, H₀ é verdadeira e a proporção é o <b>erro tipo I</b>: o esperado é ficar perto de "
            f"{fmt(100 * alpha, 0)}%."
        )
        if not SITUACOES[situacao].mede_erro_tipo_1:
            leitura += f" Nesta situação, só para o {mw}: as médias diferem, e a H₀ do {welch} é falsa."
    else:
        # O teste com mais poder vem primeiro na frase
        primeiro, segundo = (mw, welch) if diferenca >= 0 else (welch, mw)
        leitura = (
            f"<b>Se o bot realmente deixasse os merges {vezes(multiplicador)} vezes mais lentos</b> e fossem "
            f"coletados {n} PRs de cada grupo, o {primeiro} perceberia a diferença "
            f"{chance_em_coletas(ponto.loc[primeiro, 'proporcao'])}, e o {segundo}, "
            f"{chance_em_coletas(ponto.loc[segundo, 'proporcao'])}"
        )
        if abs(diferenca) <= margem:
            leitura += ": os dois testes se saem igualmente bem aqui."
        elif primeiro == mw:
            leitura += f", porque os poucos PRs muito lentos inflam a variância do {welch} e escondem a diferença."
        else:
            leitura += ", porque, com dados simétricos, a média resume bem cada grupo."
    if alpha == ALPHA_ESTRITO:
        leitura += (
            f" Com α = {fmt(alpha, 2)}, os testes exigem mais evidência para rejeitar H₀: há menos alarmes "
            "falsos, mas também menos detecções."
        )

    st.markdown(
        f"""
        <div class="power-kpis">
          {cartoes}
          <div><span class="key">Diferença ({mw} − {welch})</span>
          <b>{"+" if diferenca > 0 else ""}{fmt(100 * diferenca, 1)} pontos</b>
          <small>{veredito} (± {fmt(100 * margem, 1)})</small></div>
        </div>
        <p class="table-note power-reading">{leitura}</p>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="grafico-interativo"):
        st.plotly_chart(
            grafico_poder_interativo(por_efeito, por_n, n, efeito, multiplicador, alpha),
            theme=None,
            config={"displayModeBar": False},
        )

    margem_maxima = fmt(100 * Z_95 * np.sqrt(0.25 / N_SIMULACOES_INTERATIVO), 1)
    st.markdown(
        f"""
        <p class="table-note">Cada ponto repete a coleta {fmt(N_SIMULACOES_INTERATIVO, 0)} vezes, em vez das
        {fmt(N_SIMULACOES, 0)} do G4, para responder rápido. Por isso, os valores podem variar até
        {margem_maxima} pontos para mais ou para menos.</p>
        """,
        unsafe_allow_html=True,
    )


def com_sinal(x: float, casas: int = 2) -> str:
    return f"+{fmt(x, casas)}" if x > 0 else fmt(x, casas)


def maiuscula(texto: str) -> str:
    # capitalize() poria o resto em minúsculas: "H₀" viraria "h₀"
    return texto[:1].upper() + texto[1:]


def direcao(efeito: float) -> str:
    return "merge mais lento com bot" if efeito > 0 else "merge mais rápido com bot"


def conteudo_dados_reais() -> None:
    welch = TESTE_PARAMETRICO
    mw = TESTE_NAO_PARAMETRICO
    reais = testes_reais()
    amostra, n_sem, n_com, _ = reais["Amostra"]
    elegiveis, n_sem_el, n_com_el, deslocamento = reais["Elegíveis"]

    poder_real = {t: poder_no_efeito_real(t) for t in (welch, mw)}

    def p(resultados: pd.DataFrame, teste: str) -> str:
        return fmt(resultados.loc[teste, "p_valor"], 3)

    def efeito(resultados: pd.DataFrame, teste: str) -> str:
        return com_sinal(resultados.loc[teste, "efeito"])

    def decisao(resultados: pd.DataFrame, teste: str) -> str:
        return "rejeita H₀" if resultados.loc[teste, "rejeita_h0"] else "não rejeita H₀"

    oposta = np.sign(amostra.loc[mw, "efeito"]) != np.sign(elegiveis.loc[mw, "efeito"])
    st.markdown(
        f"""
        <dl class="facts">
          <dt>Amostra coletada</dt>
          <dd>Com {n_sem} + {n_com} PRs, nenhum teste rejeita H₀ a α = {fmt(ALPHA, 2)}: o {mw}
          chega perto (p = {p(amostra, mw)}, r = {efeito(amostra, mw)}, {direcao(amostra.loc[mw, "efeito"])})
          e o {welch} não vê diferença (p = {p(amostra, welch)}).</dd>
          <dt>Todos os elegíveis</dt>
          <dd>Com os {n_sem_el + n_com_el} PRs, o {mw} {decisao(elegiveis, mw)} (p = {p(elegiveis, mw)}),
          {"mas na direção oposta à da amostra" if oposta else "na mesma direção da amostra"}
          (r = {efeito(elegiveis, mw)}, {direcao(elegiveis.loc[mw, "efeito"])}), e o {welch}
          {decisao(elegiveis, welch)} (p = {p(elegiveis, welch)}).</dd>
          <dt>O que isso indica</dt>
          <dd>O efeito real é pequeno, cerca de {fmt(abs(deslocamento), 2)} desvio no log: com
          {N_POR_GRUPO} PRs por grupo, a simulação dá ao {mw} só {fmt(100 * poder_real[mw], 0)}% de
          chance de detectá-lo, e ao {welch}, {fmt(100 * poder_real[welch], 0)}%. Não rejeitar H₀ na
          amostra não mostra que o bot é indiferente, só que ela é pequena demais.</dd>
        </dl>
        """,
        unsafe_allow_html=True,
    )

    simbolos = {welch: "t", mw: "U"}
    abreviacoes = {"g de Hedges": "g", "rank-biserial": "r"}
    linhas = {
        "Estatística": lambda r, t: (
            f"<span class='unit'>{simbolos[t]}</span> {fmt(r.loc[t, 'estatistica'], 2 if t == welch else 1)}"
        ),
        "P-valor": p,
        "Tamanho do efeito": lambda r, t: (
            f"<span class='unit'>{abreviacoes[r.loc[t, 'medida_efeito']]}</span> {efeito(r, t)}"
        ),
        "Com bot, o merge é": lambda r, t: (
            f"<span class='txt'>{'mais lento' if r.loc[t, 'efeito'] > 0 else 'mais rápido'}</span>"
        ),
        f"Conclusão (α = {fmt(ALPHA, 2)})": lambda r, t: (
            f"<span class='badge{' badge-on' if r.loc[t, 'rejeita_h0'] else ''}'>"
            f"{maiuscula(decisao(r, t))}</span>"
        ),
    }

    def tabela(titulo: str, r: pd.DataFrame) -> str:
        corpo = "".join(
            f"<tr><th>{rotulo}</th>" + "".join(f"<td>{celula(r, t)}</td>" for t in (welch, mw)) + "</tr>"
            for rotulo, celula in linhas.items()
        )
        return (
            f"<div class='table-scroll'><table class='stats-table result-table'><caption>{titulo}</caption>"
            f"<thead><tr><th></th><th>{welch}</th><th>{mw}</th></tr></thead><tbody>{corpo}</tbody></table></div>"
        )

    st.markdown(
        f"""
        <div class="tables-pair">
          {tabela(f"Amostra do laboratório ({n_sem} + {n_com} PRs)", amostra)}
          {tabela(f"Todos os elegíveis ({n_sem_el} + {n_com_el} PRs)", elegiveis)}
        </div>
        <p class="table-note">g de Hedges (Welch) e r rank-biserial (Mann-Whitney): valores positivos
        indicam tempos maiores com bot. A amostra foi sorteada dos elegíveis com a semente {SEED}.</p>
        """,
        unsafe_allow_html=True,
    )


def conteudo_conclusao() -> None:
    welch = TESTE_PARAMETRICO
    mw = TESTE_NAO_PARAMETRICO
    erro = erro_tipo_1(simulacoes(), ALPHA).set_index(["situacao", "teste"])
    taxas_mw = erro.xs(mw, level="teste")["proporcao"]
    curvas = curvas_poder()
    multiplicador = np.exp(EFEITO_EXEMPLO * calibrar().sigma)
    vantagem_normal, _, welch_ganha = vantagem_welch_no_controle()
    amostra = testes_reais()["Amostra"][0]

    # O Welch só "ganha" numa violação se superar o Mann-Whitney além da margem de erro
    welch_ganha_em_violacao = any(
        poder(s, welch, e) - poder(s, mw, e)
        > np.hypot(*(curvas.loc[(s, t, e), "margem_erro"] for t in (welch, mw)))
        for s in SITUACOES
        if s != "normal"
        for e in efeitos_simulados()
        if e > 0
    )
    rejeicoes_amostra = int(amostra["rejeita_h0"].sum())

    st.markdown(
        f"""
        <div class="hyp">
          <div>
            <span class="hyp-label">Antes de simular</span>
            <p>Esperávamos que o <b>{mw}</b> se saísse melhor, porque os tempos até o merge são
            assimétricos e têm outliers, que inflam a variância e tiram poder do {welch}.</p>
          </div>
          <div>
            <span class="hyp-label">Depois de simular</span>
            <p>A expectativa se confirmou, com mais folga do que prevíamos: no cenário principal, com
            tempos {fmt(multiplicador, 1)} vezes maiores com bot, o {mw} detecta o efeito em
            {fmt(100 * poder(SITUACAO_EXEMPLO, mw), 0)}% dos conjuntos, contra
            {fmt(100 * poder(SITUACAO_EXEMPLO, welch), 0)}% do {welch}.</p>
          </div>
        </div>

        <dl class="facts">
          <dt>O que não prevíamos</dt>
          <dd>Sob H₀, o {welch} não erra mais do que promete, e sim menos:
          {fmt(100 * erro.loc[(SITUACAO_EXEMPLO, welch), "proporcao"], 1)}% de erro tipo I no cenário
          principal, em vez de {fmt(100 * ALPHA, 0)}%, um teste conservador que paga essa cautela em
          poder (seções 4 e 5).</dd>
          <dt>Recomendação</dt>
          <dd><b>Usar o {mw}</b> para comparar tempos até o merge: ele manteve o erro tipo I entre
          {fmt(100 * taxas_mw.min(), 1)}% e {fmt(100 * taxas_mw.max(), 1)}% em todas as situações e
          {"não perdeu poder em nenhuma violação" if not welch_ganha_em_violacao
           else "teve mais poder na maior parte das violações"}.</dd>
          <dt>Quando a escolha mudaria</dt>
          <dd>O {welch} só passa à frente com dados próximos da normal, como o log dos tempos no controle,
          e mesmo assim por até {fmt(100 * vantagem_normal, 1)}
          {"pontos" if welch_ganha else "pontos, dentro da margem de erro"}; ele também é a escolha se a pergunta for
          sobre a média em horas, como o tempo total de espera, que o {mw}, por comparar postos, não testa.</dd>
          <dt>E nos dados reais</dt>
          <dd>{"Nenhum teste rejeita" if rejeicoes_amostra == 0 else "Só parte dos testes rejeita"} H₀ na
          amostra de {N_POR_GRUPO} PRs por grupo, mas, com o efeito observado, o {mw} teria só
          {fmt(100 * poder_no_efeito_real(mw), 0)}% de poder (seção 6); e, como a comparação é antes ×
          depois da adoção, mesmo uma diferença não poderia ser atribuída só ao bot.</dd>
        </dl>
        """,
        unsafe_allow_html=True,
    )


# Seções já escritas; as demais mostram o aviso de pendente
CONTEUDOS = {
    "cenario": conteudo_cenario,
    "dados": conteudo_dados,
    "testes": conteudo_testes,
    "erro-tipo-1": conteudo_erro_tipo_1,
    "poder": conteudo_poder,
    "dados-reais": conteudo_dados_reais,
    "conclusao": conteudo_conclusao,
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
