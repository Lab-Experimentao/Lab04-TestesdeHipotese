"""Gerador de dados simulados calibrado nos dados reais de tempo até o merge.

A calibração usa todos os PRs elegíveis, não só a amostra de 60: com 845 observações, os
parâmetros são mais estáveis e a cauda direita fica bem representada. Os dois grupos são
reunidos para que, com efeito zero, tenham a mesma distribuição (H₀ verdadeira).

As situações cobrem o controle, em que o Welch tem os pressupostos atendidos, e as violações da
pergunta Q3: assimetria, outliers e amostra pequena. Cada uma altera um aspecto por vez, para que
a diferença em relação à situação de origem possa ser atribuída a ele.
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy import stats

from src.config import RAW_DATA_DIR

ARQUIVO_ELEGIVEIS = RAW_DATA_DIR / "prs_elegiveis.csv"

# A coleta guarda as horas com duas casas: 0,01 h é o menor valor mensurável
RESOLUCAO_H = 0.01
# Parcela do grupo menor na situação desbalanceada
PARCELA_MENOR = 0.25
ITERACOES_EM = 500
# Observações por grupo: o tamanho da amostra real e o da situação de amostra pequena
N_POR_GRUPO = 30
N_PEQUENO = 10
# A parcela de outliers é a de PRs reais parados por mais de uma semana
LIMIAR_OUTLIER_H = 168


@dataclass(frozen=True)
class Situacao:
    """Uma situação simulada e a justificativa para incluí-la."""

    nome: str
    descricao: str
    pressuposto: str              # o que ela viola no teste paramétrico
    justificativa: str
    n: int = N_POR_GRUPO          # observações por grupo a passar para gerar_conjunto
    escala_log: bool = False      # gera o log das horas, em vez das horas
    mede_erro_tipo_1: bool = True  # com efeito zero, H₀ é verdadeira para os dois testes


SITUACOES = {
    "normal": Situacao(
        "Normal (controle)",
        "Normal no log dos tempos, com a mesma média e o mesmo desvio nos dois grupos",
        "Nenhum",
        "É a referência: mostra o Welch com os pressupostos atendidos e, por comparação, o que "
        "cada violação muda.",
        escala_log=True,
    ),
    "mistura": Situacao(
        "Mistura (cenário principal)",
        "Mistura de duas lognormais ajustada aos dados reais",
        "Normalidade: assimetria forte, dois picos e cauda longa",
        "É a forma observada nos PRs reais, com merges rápidos e lentos.",
    ),
    "lognormal": Situacao(
        "Lognormal",
        "Lognormal simples, mesma variância e grupos do mesmo tamanho",
        "Normalidade: assimetria forte",
        "Mantém a assimetria sem os dois picos da mistura, para separar o efeito de cada um.",
    ),
    "outliers": Situacao(
        "Outliers",
        "Controle com uma parcela dos PRs deslocada para a direita",
        "Normalidade: outliers à direita",
        "Representa PRs esquecidos por semanas. Parte do controle para isolar os outliers, com "
        "assimetria bem menor que a das outras violações.",
        escala_log=True,
    ),
    "amostra_pequena": Situacao(
        "Amostra pequena",
        "Mistura do cenário principal, com menos PRs por grupo",
        "Normalidade da média: poucas observações para o Teorema Central do Limite",
        "Representa projetos pequenos ou janelas curtas de coleta, em que um único PR lento pesa "
        "ainda mais na média.",
        n=N_PEQUENO,
    ),
    "desbalanceado": Situacao(
        "Grupos desiguais",
        "Lognormal simples e grupos de tamanhos diferentes (1:3)",
        "Simetria do t: a assimetria dos grupos deixa de se cancelar",
        "Representa a adoção parcial do bot, que deixa um grupo bem maior que o outro.",
    ),
    "variancias_diferentes": Situacao(
        "Variâncias diferentes",
        "Lognormal simples, com o desvio do log observado em cada grupo",
        "Nenhum além da assimetria: o Welch aceita variâncias diferentes",
        "Testa a situação para a qual o Welch foi criado. Só serve para o poder: com efeito zero, "
        "as medianas são iguais, mas as médias não.",
        # O H₀ do Mann-Whitney continua verdadeiro e o do Welch não
        mede_erro_tipo_1=False,
    ),
}

# Situações sorteadas da mistura ajustada; as demais usam uma única normal no log
SITUACOES_MISTURA = ("mistura", "amostra_pequena")


@dataclass(frozen=True)
class Calibracao:
    """Parâmetros, na escala do log, extraídos dos dados reais."""

    mu: float               # log da mediana
    sigma: float            # desvio do log
    sigma_sem_bot: float
    sigma_com_bot: float
    peso_lento: float       # peso do componente lento da mistura
    mu_rapido: float
    sigma_rapido: float
    mu_lento: float
    sigma_lento: float
    parcela_outlier: float       # parcela de PRs acima de LIMIAR_OUTLIER_H
    deslocamento_outlier: float  # distância do PR mais lento até a mediana, em desvios (sigma)


def ajustar_mistura(x: np.ndarray) -> tuple[float, float, float, float, float]:
    """Ajusta duas normais por EM. Retorna (peso_lento, mu_rapido, sigma_rapido, mu_lento, sigma_lento)."""
    pesos = np.array([0.5, 0.5])
    mus = np.quantile(x, [0.25, 0.75])
    sigmas = np.full(2, x.std(ddof=1) / 2)
    for _ in range(ITERACOES_EM):
        densidades = pesos * stats.norm.pdf(x[:, None], mus, sigmas)
        responsabilidades = densidades / densidades.sum(axis=1, keepdims=True)
        total = responsabilidades.sum(axis=0)
        pesos = total / len(x)
        mus = (responsabilidades * x[:, None]).sum(axis=0) / total
        sigmas = np.sqrt((responsabilidades * (x[:, None] - mus) ** 2).sum(axis=0) / total)
    return float(pesos[1]), float(mus[0]), float(sigmas[0]), float(mus[1]), float(sigmas[1])


@lru_cache(maxsize=1)
def calibrar() -> Calibracao:
    df = pd.read_csv(ARQUIVO_ELEGIVEIS)
    horas = df["horas_ate_merge"]
    log_horas = np.log(horas)
    desvios = log_horas.groupby(df["grupo"]).std(ddof=1)
    mu = float(np.log(horas.median()))
    sigma = float(log_horas.std(ddof=1))
    return Calibracao(
        mu,
        sigma,
        float(desvios["sem_bot"]),
        float(desvios["com_bot"]),
        *ajustar_mistura(log_horas.to_numpy()),
        float((horas > LIMIAR_OUTLIER_H).mean()),
        float((log_horas.max() - mu) / sigma),
    )


def _sortear_log(n: int, situacao: str, sigma: float, c: Calibracao, rng: np.random.Generator) -> np.ndarray:
    if situacao in SITUACOES_MISTURA:
        lento = rng.random(n) < c.peso_lento
        return rng.normal(
            np.where(lento, c.mu_lento, c.mu_rapido),
            np.where(lento, c.sigma_lento, c.sigma_rapido),
        )
    log_x = rng.normal(c.mu, sigma, n)
    if situacao == "outliers":
        log_x += (rng.random(n) < c.parcela_outlier) * c.deslocamento_outlier * c.sigma
    return log_x


def gerar_conjunto(
    n: int,
    efeito: float,
    situacao: str,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Gera os tempos até o merge dos grupos (sem_bot, com_bot).

    n: observações por grupo (SITUACOES[situacao].n); na situação desbalanceada, 2n são
        divididas em 1:3.
    efeito: deslocamento de com_bot no log, em desvios (sigma), o mesmo em todas as situações.
        Antes do arredondamento, os tempos de com_bot ficam multiplicados por
        exp(efeito · sigma); efeito > 0 significa merge mais lento com o bot.
    situacao: uma das chaves de SITUACOES.
    rng: use get_rng() de src.config, para manter a reprodutibilidade.

    Os tempos são em horas, arredondados como na coleta, o que reproduz os empates dos dados
    reais. Nas situações com escala_log, são o log das horas, sem arredondamento: os testes são
    aplicados diretamente a esses valores, que podem ser negativos.
    """
    if situacao not in SITUACOES:
        raise ValueError(f"Situação desconhecida: {situacao}. Opções: {list(SITUACOES)}")

    c = calibrar()
    n_sem, n_com = n, n
    sigma_sem, sigma_com = c.sigma, c.sigma
    if situacao == "desbalanceado":
        n_sem = round(2 * n * PARCELA_MENOR)
        n_com = 2 * n - n_sem
    elif situacao == "variancias_diferentes":
        sigma_sem, sigma_com = c.sigma_sem_bot, c.sigma_com_bot

    log_sem = _sortear_log(n_sem, situacao, sigma_sem, c, rng)
    log_com = _sortear_log(n_com, situacao, sigma_com, c, rng) + efeito * c.sigma

    if SITUACOES[situacao].escala_log:
        return log_sem, log_com
    return tuple(np.maximum(np.exp(x).round(2), RESOLUCAO_H) for x in (log_sem, log_com))
