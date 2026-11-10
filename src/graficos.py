"""Gráficos do dashboard, em Plotly."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config import (
    COR_REAL,
    COR_REJEICAO,
    COR_SIMULADO,
    CORES_TESTES,
    NOMES_GRUPOS,
    TESTE_NAO_PARAMETRICO,
    COR_REFERENCIA,
    TESTE_PARAMETRICO,
)
from src.monte_carlo import FAIXA_ACEITAVEL
from src.simulacao import SITUACOES
from src.testes import ReferenciaH0

# Mesmos tons de assets/style.css
FONTE = "Inter, system-ui, sans-serif"
COR_TEXTO = "#111113"
COR_SUAVE = "#6b6b76"
COR_GRADE = "#e7e7ea"

# Largura dos bins do G1 em log10: meia década
BIN_LOG10 = 0.5
# Folga acima da barra mais alta, onde fica o rótulo da mediana
FOLGA_Y = 1.25

# Eixo x do G2, em desvios-padrão da distribuição de referência, e bins por desvio
ALCANCE_G2 = 4
BINS_POR_DESVIO_G2 = 4
PONTOS_CURVA = 400

# Fim do eixo x do G3 (%) e distância de cada teste ao centro da linha da situação
FIM_X_G3 = 8
DESLOCAMENTO_G3 = {TESTE_PARAMETRICO: -0.16, TESTE_NAO_PARAMETRICO: 0.16}
SIMBOLOS_G3 = {TESTE_PARAMETRICO: "circle", TESTE_NAO_PARAMETRICO: "diamond"}

# Grade do G4: uma situação por painel; a célula que sobra recebe a legenda
COLUNAS_G4 = 4
PODER_ALVO = 0.8


def fmt(x: float, casas: int = 1) -> str:
    """Número no formato brasileiro: 1.234,5"""
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _limite_bin(horas: float) -> str:
    return fmt(horas, 2 if horas < 1 else 1 if horas < 10 else 0)


def g1_real_simulado(reais: pd.DataFrame, simulados: pd.DataFrame) -> go.Figure:
    """Histograma de cada grupo: dados reais à esquerda, simulados à direita.

    Os dois DataFrames têm as colunas grupo e horas_ate_merge. O tempo é muito assimétrico, então
    o eixo x fica em log10; os bins e os eixos são os mesmos nos quatro painéis, para comparar
    as alturas diretamente.
    """
    grupos = list(NOMES_GRUPOS)
    colunas = [("Reais", reais, COR_REAL), ("Simulados", simulados, COR_SIMULADO)]

    log_horas = np.log10(pd.concat([reais, simulados])["horas_ate_merge"])
    inicio = np.floor(log_horas.min() / BIN_LOG10) * BIN_LOG10
    fim = np.ceil(log_horas.max() / BIN_LOG10) * BIN_LOG10
    bins = np.arange(inicio, fim + BIN_LOG10, BIN_LOG10)

    titulos = [
        f"{NOMES_GRUPOS[g]} · {nome.lower()} (n = {(df['grupo'] == g).sum()})"
        for g in grupos
        for nome, df, _ in colunas
    ]
    fig = make_subplots(
        rows=len(grupos),
        cols=len(colunas),
        shared_xaxes=True,
        shared_yaxes=True,
        horizontal_spacing=0.07,
        vertical_spacing=0.09,
        subplot_titles=titulos,
    )

    maior_contagem = 0
    for linha, g in enumerate(grupos, start=1):
        for coluna, (nome, df, cor) in enumerate(colunas, start=1):
            horas = df.loc[df["grupo"] == g, "horas_ate_merge"]
            contagens, _ = np.histogram(np.log10(horas), bins)
            maior_contagem = max(maior_contagem, contagens.max())
            limites = 10 ** bins
            fig.add_trace(
                go.Bar(
                    x=(bins[:-1] + bins[1:]) / 2,
                    y=contagens,
                    name=nome,
                    legendgroup=nome,
                    showlegend=linha == 1,
                    marker={"color": cor},
                    customdata=[
                        (_limite_bin(a), _limite_bin(b))
                        for a, b in zip(limites[:-1], limites[1:])
                    ],
                    hovertemplate=(
                        "%{customdata[0]} a %{customdata[1]} h<br>"
                        f"%{{y}} PRs<extra>{NOMES_GRUPOS[g]} · {nome.lower()}</extra>"
                    ),
                ),
                row=linha,
                col=coluna,
            )
            mediana = horas.median()
            fig.add_vline(
                x=np.log10(mediana),
                row=linha,
                col=coluna,
                line={"color": COR_TEXTO, "width": 1},
                annotation_text=f"mediana {fmt(mediana, 2)} h",
                annotation_position="top right",
                annotation_font={"size": 12, "color": COR_TEXTO},
            )

    decadas = np.arange(np.ceil(inicio), np.floor(fim) + 1)
    fig.update_xaxes(
        range=[inicio, fim],
        tickvals=decadas,
        ticktext=[fmt(10.0 ** d, max(0, int(-d))) for d in decadas],
        ticks="outside",
        tickcolor=COR_GRADE,
        linecolor=COR_GRADE,
        showgrid=False,
        zeroline=False,
        fixedrange=True,
    )
    fig.update_xaxes(title_text="Tempo até o merge (horas, escala log)", row=len(grupos))
    fig.update_yaxes(
        range=[0, maior_contagem * FOLGA_Y],
        dtick=5,
        gridcolor=COR_GRADE,
        zeroline=False,
        fixedrange=True,
    )
    fig.update_yaxes(title_text="Número de PRs", col=1)
    fig.update_layout(
        title={
            "text": "G1. Tempo até o merge por grupo: dados reais × simulados",
            "x": 0,
            "xanchor": "left",
            "font": {"size": 16, "color": COR_TEXTO},
        },
        legend={"orientation": "h", "x": 1, "xanchor": "right", "y": 1.13, "yanchor": "top"},
        font={"family": FONTE, "size": 12, "color": COR_SUAVE},
        height=580,
        margin={"l": 56, "r": 24, "t": 88, "b": 56},
        bargap=0.04,
        barcornerradius=4,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        hoverlabel={"font_family": FONTE},
    )
    fig.update_annotations(font_family=FONTE)
    return fig


def _rgba(cor: str, opacidade: float) -> str:
    r, g, b = (int(cor[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{opacidade})"


def _area_caudas(
    fig: go.Figure,
    referencia: ReferenciaH0,
    distancia: float,
    alcance: float,
    coluna: int,
    mostrar_legenda: bool,
    **estilo,
) -> None:
    """Preenche sob a curva as duas caudas além de centro ± distancia."""
    for lado in (-1, 1):
        x = referencia.centro + lado * np.linspace(distancia, alcance, PONTOS_CURVA)
        fig.add_trace(
            go.Scatter(
                x=x,
                y=referencia.distribuicao.pdf(x),
                mode="lines",
                line={"width": 0},
                fill="tozeroy",
                showlegend=mostrar_legenda and lado == -1,
                hoverinfo="skip",
                **estilo,
            ),
            row=1,
            col=coluna,
        )


def g2_estatistica_h0(
    exemplo: pd.DataFrame,
    referencias: dict[str, ReferenciaH0],
    simulacoes: dict[str, pd.DataFrame],
    alpha: float,
) -> go.Figure:
    """Distribuição da estatística de cada teste sob H₀, com região de rejeição e p-valor do exemplo.

    exemplo: resultado de aplicar_testes no conjunto de exemplo.
    referencias: distribuição em que cada teste se baseia; as áreas sob ela são α e o p-valor.
    simulacoes: estatísticas em conjuntos simulados com efeito zero, para comparar com a curva.
    """
    t_critico = referencias[TESTE_PARAMETRICO].limites_criticos[1]
    u_menor, u_maior = referencias[TESTE_NAO_PARAMETRICO].limites_criticos
    pares = 2 * referencias[TESTE_NAO_PARAMETRICO].centro
    paineis = {
        TESTE_PARAMETRICO: (
            "t",
            2,
            f"t de Welch · rejeita H₀ se |t| > {fmt(t_critico, 2)}",
            "Estatística t (erros-padrão)",
        ),
        TESTE_NAO_PARAMETRICO: (
            "U",
            1,
            f"Mann-Whitney · rejeita H₀ se U < {fmt(u_menor, 0)} ou U > {fmt(u_maior, 0)}",
            f"Estatística U (pares, de {fmt(pares, 0)}, com bot mais lento)",
        ),
    }
    fig = make_subplots(
        rows=1,
        cols=len(paineis),
        horizontal_spacing=0.09,
        subplot_titles=[titulo for _, _, titulo, _ in paineis.values()],
    )

    for coluna, (teste, (simbolo, casas, _, eixo_x)) in enumerate(paineis.items(), start=1):
        referencia = referencias[teste]
        cor = CORES_TESTES[teste]
        centro = referencia.centro
        alcance = ALCANCE_G2 * referencia.distribuicao.std()
        inicio, fim = centro - alcance, centro + alcance

        estatisticas = simulacoes[teste]["estatistica"]
        bins = np.linspace(inicio, fim, 2 * ALCANCE_G2 * BINS_POR_DESVIO_G2 + 1)
        contagens, _ = np.histogram(estatisticas, bins)
        densidades = contagens / (len(estatisticas) * (bins[1] - bins[0]))
        fig.add_trace(
            go.Bar(
                x=(bins[:-1] + bins[1:]) / 2,
                y=densidades,
                name=f"Simulação ({fmt(len(estatisticas), 0)} conjuntos)",
                legendgroup="simulacao",
                legendrank=1,
                showlegend=coluna == 1,
                marker={"color": COR_SIMULADO},
                customdata=[
                    (fmt(a, casas), fmt(b, casas), fmt(100 * c / len(estatisticas), 1))
                    for a, b, c in zip(bins[:-1], bins[1:], contagens)
                ],
                hovertemplate=(
                    f"{simbolo} de %{{customdata[0]}} a %{{customdata[1]}}<br>"
                    "%{customdata[2]}% dos conjuntos<extra>Simulação sob H₀</extra>"
                ),
            ),
            row=1,
            col=coluna,
        )

        for x0, x1 in (
            (inicio, centro - referencia.distancia_critica),
            (centro + referencia.distancia_critica, fim),
        ):
            fig.add_vrect(
                x0=x0,
                x1=x1,
                row=1,
                col=coluna,
                fillcolor=COR_REJEICAO,
                opacity=0.07,
                line_width=0,
                layer="below",
            )
        _area_caudas(
            fig,
            referencia,
            referencia.distancia_critica,
            alcance,
            coluna,
            coluna == 1,
            name=f"Região de rejeição (α = {fmt(alpha, 2)})",
            legendgroup="rejeicao",
            legendrank=4,
            fillcolor=_rgba(COR_REJEICAO, 0.45),
        )
        _area_caudas(
            fig,
            referencia,
            referencia.distancia_p,
            alcance,
            coluna,
            True,
            name=f"P-valor: {teste}",
            legendgroup=f"p-{teste}",
            legendrank=3 * coluna,
            fillpattern={
                "shape": "/",
                "fgcolor": cor,
                "bgcolor": "rgba(255,255,255,0)",
                "size": 7,
                "solidity": 0.35,
            },
        )

        x = np.linspace(inicio, fim, PONTOS_CURVA)
        y = referencia.distribuicao.pdf(x)
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                line={"color": cor, "width": 2},
                name=f"Curva sob H₀: {teste}",
                legendgroup=f"curva-{teste}",
                legendrank=3 * coluna - 1,
                hoverinfo="skip",
            ),
            row=1,
            col=coluna,
        )

        observado = exemplo.loc[teste, "estatistica"]
        fig.add_vline(
            x=2 * centro - observado,
            row=1,
            col=coluna,
            line={"color": COR_SUAVE, "width": 1},
        )
        fig.add_vline(
            x=observado,
            row=1,
            col=coluna,
            line={"color": COR_TEXTO, "width": 1},
            annotation_text=(
                f"{simbolo} = {fmt(observado, casas)} · p = {fmt(exemplo.loc[teste, 'p_valor'], 3)}"
            ),
            annotation_position="top left",
            annotation_font={"size": 12, "color": COR_TEXTO},
        )

        fig.update_xaxes(
            title_text=eixo_x,
            range=[inicio, fim],
            ticks="outside",
            tickcolor=COR_GRADE,
            linecolor=COR_GRADE,
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            row=1,
            col=coluna,
        )
        fig.update_yaxes(
            title_text=f"Densidade (por unidade de {simbolo})",
            range=[0, max(y.max(), densidades.max()) * FOLGA_Y],
            gridcolor=COR_GRADE,
            zeroline=False,
            fixedrange=True,
            row=1,
            col=coluna,
        )

    fig.update_layout(
        title={
            "text": "G2. Estatística de cada teste sob H₀: região de rejeição e p-valor do exemplo",
            "x": 0,
            "xanchor": "left",
            "font": {"size": 16, "color": COR_TEXTO},
        },
        legend={
            "orientation": "h",
            "x": 0,
            "xanchor": "left",
            "y": -0.2,
            "yanchor": "top",
            # Três colunas: simulação e rejeição, curvas, p-valores
            "entrywidth": 0.32,
            "entrywidthmode": "fraction",
        },
        font={"family": FONTE, "size": 12, "color": COR_SUAVE},
        height=540,
        margin={"l": 64, "r": 24, "t": 88, "b": 110},
        bargap=0.04,
        separators=",.",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        hoverlabel={"font_family": FONTE},
    )
    fig.update_annotations(font_family=FONTE)
    return fig


def g3_erro_tipo_1(erro: pd.DataFrame, alpha: float) -> go.Figure:
    """Erro tipo I de cada teste por situação, com a linha em α e a faixa aceitável.

    erro: resultado de erro_tipo_1. Um teste fica de fora da situação em que seu H₀ é falso.
    """
    posicoes = {situacao: i for i, situacao in enumerate(SITUACOES)}
    limites_y = [-0.5, len(posicoes) - 0.5]
    faixa = [100 * alpha * limite for limite in FAIXA_ACEITAVEL]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[faixa[0], faixa[1], faixa[1], faixa[0]],
            y=[limites_y[0], limites_y[0], limites_y[1], limites_y[1]],
            mode="none",
            fill="toself",
            fillcolor=_rgba(COR_SIMULADO, 0.18),
            name=f"Faixa aceitável ({fmt(faixa[0], 1)}% a {fmt(faixa[1], 1)}%)",
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[100 * alpha] * 2,
            y=limites_y,
            mode="lines",
            line={"color": COR_REFERENCIA, "width": 1.5},
            name=f"{fmt(100 * alpha, 0)}% esperados",
            hoverinfo="skip",
        )
    )

    for teste, cor in CORES_TESTES.items():
        linhas = erro[(erro["teste"] == teste) & erro["h0_verdadeira"]]
        y = linhas["situacao"].map(posicoes) + DESLOCAMENTO_G3[teste]
        fig.add_trace(
            go.Scatter(
                x=100 * linhas["proporcao"],
                y=y,
                mode="markers",
                name=teste,
                marker={
                    "color": cor,
                    "size": 12,
                    "symbol": SIMBOLOS_G3[teste],
                    "line": {"color": "#ffffff", "width": 2},
                },
                error_x={
                    "type": "data",
                    "array": 100 * linhas["margem_erro"],
                    "color": cor,
                    "thickness": 1.5,
                    "width": 4,
                },
                customdata=[
                    (SITUACOES[s].nome, fmt(100 * p, 2), fmt(100 * m, 2), d)
                    for s, p, m, d in zip(
                        linhas["situacao"], linhas["proporcao"], linhas["margem_erro"], linhas["diagnostico"]
                    )
                ],
                hovertemplate=(
                    "%{customdata[0]}<br>%{customdata[1]}% ± %{customdata[2]}<br>"
                    f"%{{customdata[3]}}<extra>{teste}</extra>"
                ),
            )
        )
        # Só os desvios ganham rótulo: a tabela abaixo do gráfico traz todos os valores
        for p, m, posicao in zip(linhas["proporcao"], linhas["margem_erro"], y):
            if not faixa[0] <= 100 * p <= faixa[1]:
                fig.add_annotation(
                    x=100 * (p + m),
                    y=posicao,
                    text=f"{fmt(100 * p, 1)}%",
                    showarrow=False,
                    xanchor="left",
                    xshift=8,
                    font={"size": 12, "color": COR_TEXTO},
                )

    for linha in erro[~erro["h0_verdadeira"]].itertuples():
        fig.add_annotation(
            x=0.1,
            y=posicoes[linha.situacao] + DESLOCAMENTO_G3[linha.teste],
            text=f"{linha.teste}: H₀ falsa aqui, não é erro tipo I",
            showarrow=False,
            xanchor="left",
            font={"size": 11, "color": COR_SUAVE},
        )

    fig.update_xaxes(
        title_text=f"Erro tipo I (% de conjuntos sem efeito com p < {fmt(alpha, 2)})",
        range=[0, FIM_X_G3],
        dtick=1,
        ticksuffix="%",
        ticks="outside",
        tickcolor=COR_GRADE,
        linecolor=COR_GRADE,
        gridcolor=COR_GRADE,
        zeroline=False,
        fixedrange=True,
    )
    fig.update_yaxes(
        title_text="Situação simulada",
        title_standoff=16,
        tickvals=list(posicoes.values()),
        ticktext=[SITUACOES[situacao].nome for situacao in posicoes],
        range=limites_y[::-1],
        showgrid=False,
        zeroline=False,
        ticklen=0,
        fixedrange=True,
        tickfont={"color": COR_TEXTO},
    )
    fig.update_layout(
        title={
            "text": f"G3. Erro tipo I dos dois testes em cada situação (α = {fmt(alpha, 2)})",
            "x": 0,
            "xanchor": "left",
            "font": {"size": 16, "color": COR_TEXTO},
        },
        legend={"orientation": "h", "x": 0, "xanchor": "left", "y": -0.16, "yanchor": "top"},
        font={"family": FONTE, "size": 12, "color": COR_SUAVE},
        height=560,
        margin={"l": 210, "r": 24, "t": 56, "b": 88},
        separators=",.",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        hoverlabel={"font_family": FONTE},
    )
    fig.update_annotations(font_family=FONTE)
    return fig


def g4_poder(simulacoes: pd.DataFrame, alpha: float, efeito_real: float | None = None) -> go.Figure:
    """Curvas de poder dos dois testes, um painel por situação, com a linha de 80%.

    simulacoes: resultado de carregar_simulacoes. No efeito zero, o ponto é o erro tipo I do G3.
    efeito_real: deslocamento observado nos dados reais, em módulo, marcado em todos os painéis.
    """
    dados = simulacoes[simulacoes["alpha"] == alpha]
    situacoes = list(SITUACOES)
    linhas_grade = -(-len(situacoes) // COLUNAS_G4)
    specs = [
        [{} if linha * COLUNAS_G4 + coluna < len(situacoes) else None for coluna in range(COLUNAS_G4)]
        for linha in range(linhas_grade)
    ]
    fig = make_subplots(
        rows=linhas_grade,
        cols=COLUNAS_G4,
        specs=specs,
        shared_yaxes=True,
        horizontal_spacing=0.035,
        vertical_spacing=0.16,
        subplot_titles=[SITUACOES[s].nome for s in situacoes],
    )
    efeito_max = dados["efeito"].max()

    for i, situacao in enumerate(situacoes):
        linha, coluna = divmod(i, COLUNAS_G4)
        linha, coluna = linha + 1, coluna + 1
        for teste, cor in CORES_TESTES.items():
            curva = dados[(dados["situacao"] == situacao) & (dados["teste"] == teste)].sort_values("efeito")
            fig.add_trace(
                go.Scatter(
                    x=curva["efeito"],
                    y=100 * curva["proporcao"],
                    mode="lines+markers",
                    name=teste,
                    legendgroup=teste,
                    showlegend=i == 0,
                    line={"color": cor, "width": 2},
                    marker={
                        "color": cor,
                        "size": 7,
                        "symbol": SIMBOLOS_G3[teste],
                        "line": {"color": "#ffffff", "width": 1},
                    },
                    customdata=[
                        (fmt(e, 2), fmt(m, 1), fmt(100 * p, 1), fmt(100 * me, 1))
                        for e, m, p, me in zip(
                            curva["efeito"], curva["multiplicador"], curva["proporcao"], curva["margem_erro"]
                        )
                    ],
                    hovertemplate=(
                        "Efeito %{customdata[0]} (tempos × %{customdata[1]})<br>"
                        "Poder %{customdata[2]}% ± %{customdata[3]}"
                        f"<extra>{teste} · {SITUACOES[situacao].nome}</extra>"
                    ),
                ),
                row=linha,
                col=coluna,
            )
        fig.add_hline(
            y=100 * PODER_ALVO,
            row=linha,
            col=coluna,
            line={"color": COR_REFERENCIA, "width": 1, "dash": "dash"},
        )
        if efeito_real is not None:
            fig.add_vline(
                x=efeito_real,
                row=linha,
                col=coluna,
                line={"color": COR_SUAVE, "width": 1, "dash": "dot"},
            )

    # Entradas só de legenda para as linhas de referência
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="lines", name=f"{fmt(100 * PODER_ALVO, 0)}% de poder",
        line={"color": COR_REFERENCIA, "width": 1, "dash": "dash"},
    ))
    if efeito_real is not None:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="lines", name=f"Efeito nos dados reais ({fmt(efeito_real, 2)})",
            line={"color": COR_SUAVE, "width": 1, "dash": "dot"},
        ))

    fig.update_xaxes(
        range=[-0.1, efeito_max + 0.1],
        dtick=0.5,
        ticks="outside",
        tickcolor=COR_GRADE,
        linecolor=COR_GRADE,
        showgrid=False,
        zeroline=False,
        fixedrange=True,
    )
    fig.update_yaxes(
        range=[0, 105],
        dtick=20,
        ticksuffix="%",
        gridcolor=COR_GRADE,
        zeroline=False,
        fixedrange=True,
    )
    fig.update_yaxes(title_text="Poder (% de conjuntos com p < α)", col=1)
    # Título do eixo x em cada painel sem outro abaixo
    for i in range(len(situacoes)):
        if i + COLUNAS_G4 >= len(situacoes):
            linha, coluna = divmod(i, COLUNAS_G4)
            fig.update_xaxes(title_text="Efeito (desvios no log)", row=linha + 1, col=coluna + 1)

    # Legenda na célula vazia da grade
    canto_x = fig.get_subplot(1, COLUNAS_G4).xaxis.domain[0]
    canto_y = fig.get_subplot(linhas_grade, 1).yaxis.domain[1]
    fig.update_layout(
        title={
            "text": f"G4. Poder dos dois testes por tamanho do efeito, em cada situação (α = {fmt(alpha, 2)})",
            "x": 0,
            "xanchor": "left",
            "font": {"size": 16, "color": COR_TEXTO},
        },
        legend={"x": canto_x + 0.02, "xanchor": "left", "y": canto_y, "yanchor": "top"},
        font={"family": FONTE, "size": 12, "color": COR_SUAVE},
        height=620,
        margin={"l": 64, "r": 24, "t": 88, "b": 56},
        separators=",.",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        hoverlabel={"font_family": FONTE},
    )
    fig.update_annotations(font_family=FONTE)
    return fig
