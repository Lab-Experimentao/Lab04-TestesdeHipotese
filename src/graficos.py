"""Gráficos do dashboard, em Plotly."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config import COR_REAL, COR_SIMULADO, NOMES_GRUPOS

# Mesmos tons de assets/style.css
FONTE = "Inter, system-ui, sans-serif"
COR_TEXTO = "#111113"
COR_SUAVE = "#6b6b76"
COR_GRADE = "#e7e7ea"

# Largura dos bins do G1 em log10: meia década
BIN_LOG10 = 0.5
# Folga acima da barra mais alta, onde fica o rótulo da mediana
FOLGA_Y = 1.25


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
