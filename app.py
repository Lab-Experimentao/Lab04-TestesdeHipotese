"""Dashboard do Lab04 - Testes de hipótese por dentro.

Execute com: streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from src.config import (
    ALPHA,
    CORES_TESTES,
    DASHBOARD_URL,
    N_SIMULACOES,
    PROJECTS_URL,
    REPO_URL,
    SEED,
)

CSS_PATH = Path(__file__).parent / "assets" / "style.css"

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


def secao(numero: int, ancora: str, titulo: str, grafico: str | None, descricao: str) -> None:
    tag = f"<span class='sec-tag'>{grafico}</span>" if grafico else ""
    st.markdown(
        f"<div class='sec-head' id='{ancora}'>"
        f"<span class='sec-num'>{numero}</span><h2>{titulo}</h2>{tag}</div>",
        unsafe_allow_html=True,
    )
    with st.container(key=f"sec-{ancora}"):
        st.markdown(
            f"<div class='pending'><b>Pendente</b>{descricao}</div>",
            unsafe_allow_html=True,
        )


aplicar_estilo()
cabecalho()
sidebar()
for i, s in enumerate(SECOES, start=1):
    secao(i, *s)
