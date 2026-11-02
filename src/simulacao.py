"""Gerador de dados simulados calibrado nos dados reais de tempo até o merge.

A calibração usa todos os PRs elegíveis, não só a amostra de 60: com 845 observações, os
parâmetros são mais estáveis e a cauda direita fica bem representada. Os dois grupos são
reunidos para que, com efeito zero, tenham a mesma distribuição (H₀ verdadeira).
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

SITUACOES = {
    "mistura": "Mistura de duas lognormais ajustada aos dados reais (cenário principal)",
    "lognormal": "Lognormal simples, mesma variância e grupos do mesmo tamanho",
    "desbalanceado": "Lognormal simples e grupos de tamanhos diferentes (1:3)",
    # Atenção: com efeito zero, as medianas são iguais, mas as médias não. O H₀ do Mann-Whitney
    # continua verdadeiro e o do Welch não, então aqui o Welch não mede erro tipo I puro.
    "variancias_diferentes": "Lognormal simples, com o desvio do log observado em cada grupo",
}


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
    return Calibracao(
        float(np.log(horas.median())),
        float(log_horas.std(ddof=1)),
        float(desvios["sem_bot"]),
        float(desvios["com_bot"]),
        *ajustar_mistura(log_horas.to_numpy()),
    )


def _sortear_log(n: int, situacao: str, sigma: float, c: Calibracao, rng: np.random.Generator) -> np.ndarray:
    if situacao != "mistura":
        return rng.normal(c.mu, sigma, n)
    lento = rng.random(n) < c.peso_lento
    return rng.normal(
        np.where(lento, c.mu_lento, c.mu_rapido),
        np.where(lento, c.sigma_lento, c.sigma_rapido),
    )


def gerar_conjunto(
    n: int,
    efeito: float,
    situacao: str,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Gera os tempos até o merge (horas) dos grupos (sem_bot, com_bot).

    n: observações por grupo; na situação desbalanceada, 2n são divididas em 1:3.
    efeito: deslocamento de com_bot no log, em desvios (sigma). Antes do arredondamento, os
        tempos de com_bot ficam multiplicados por exp(efeito · sigma); efeito > 0 significa
        merge mais lento com o bot.
    situacao: uma das chaves de SITUACOES.
    rng: use get_rng() de src.config, para manter a reprodutibilidade.

    Os tempos são arredondados como na coleta, o que reproduz os empates dos dados reais.
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

    return tuple(np.maximum(np.exp(x).round(2), RESOLUCAO_H) for x in (log_sem, log_com))
