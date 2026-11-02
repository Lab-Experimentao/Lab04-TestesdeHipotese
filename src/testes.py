"""Os dois testes do par P1, com estatística, p-valor e tamanho do efeito.

Ambos são bicaudais (seção 1 do dashboard) e tratam o primeiro grupo como referência: um
efeito positivo indica valores maiores no segundo grupo.

Execute com: python -m src.testes
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from src.config import (
    ALPHA,
    PROCESSED_DATA_DIR,
    TESTE_NAO_PARAMETRICO,
    TESTE_PARAMETRICO,
    get_rng,
)
from src.simulacao import gerar_conjunto

ARQUIVO_EXEMPLO = PROCESSED_DATA_DIR / "exemplo_simulado.csv"

# Conjunto simulado de exemplo
N_EXEMPLO = 30
EFEITO_EXEMPLO = 0.5
SITUACAO_EXEMPLO = "mistura"


@dataclass(frozen=True)
class ReferenciaH0:
    """Distribuição em que o teste se baseia sob H₀.

    As duas caudas além de centro ± distancia_critica somam α, e além de centro ± distancia_p
    somam o p-valor. correcao é o que a estatística observada ainda precisa superar além da
    distância crítica para rejeitar H₀ (correção de continuidade do Mann-Whitney).
    """

    distribuicao: stats.distributions.rv_frozen
    centro: float
    distancia_critica: float
    distancia_p: float
    correcao: float = 0.0

    @property
    def limites_criticos(self) -> tuple[float, float]:
        distancia = self.distancia_critica + self.correcao
        return self.centro - distancia, self.centro + distancia


def hedges_g(a: np.ndarray, b: np.ndarray) -> float:
    """Diferença de médias (b - a) em desvios combinados, com correção para amostras pequenas."""
    n_a, n_b = len(a), len(b)
    gl = n_a + n_b - 2
    variancia = ((n_a - 1) * a.var(ddof=1) + (n_b - 1) * b.var(ddof=1)) / gl
    return float((b.mean() - a.mean()) / np.sqrt(variancia) * (1 - 3 / (4 * gl - 1)))


def teste_welch(a: np.ndarray, b: np.ndarray) -> dict:
    r = stats.ttest_ind(b, a, equal_var=False, alternative="two-sided")
    return {
        "teste": TESTE_PARAMETRICO,
        "estatistica": float(r.statistic),
        "p_valor": float(r.pvalue),
        "efeito": hedges_g(a, b),
        "medida_efeito": "g de Hedges",
    }


def teste_mann_whitney(a: np.ndarray, b: np.ndarray) -> dict:
    r = stats.mannwhitneyu(b, a, alternative="two-sided")
    return {
        "teste": TESTE_NAO_PARAMETRICO,
        "estatistica": float(r.statistic),
        "p_valor": float(r.pvalue),
        # Rank-biserial: P(b > a) - P(b < a), entre -1 e 1
        "efeito": float(2 * r.statistic / (len(a) * len(b)) - 1),
        "medida_efeito": "rank-biserial",
    }


def aplicar_testes(a: np.ndarray, b: np.ndarray, alpha: float = ALPHA) -> pd.DataFrame:
    resultados = pd.DataFrame([teste_welch(a, b), teste_mann_whitney(a, b)])
    resultados["rejeita_h0"] = resultados["p_valor"] < alpha
    return resultados.set_index("teste")


def referencia_welch(a: np.ndarray, b: np.ndarray, alpha: float = ALPHA) -> ReferenciaH0:
    r = stats.ttest_ind(b, a, equal_var=False, alternative="two-sided")
    distribuicao = stats.t(r.df)
    return ReferenciaH0(distribuicao, 0.0, float(distribuicao.ppf(1 - alpha / 2)), abs(float(r.statistic)))


def referencia_mann_whitney(a: np.ndarray, b: np.ndarray, alpha: float = ALPHA) -> ReferenciaH0:
    """Normal que o SciPy usa neste tamanho de amostra, com as correções de empates e de continuidade."""
    n_a, n_b = len(a), len(b)
    n = n_a + n_b
    _, empates = np.unique(np.concatenate([a, b]), return_counts=True)
    variancia = n_a * n_b / 12 * (n + 1 - (empates**3 - empates).sum() / (n * (n - 1)))
    centro = n_a * n_b / 2
    distribuicao = stats.norm(centro, np.sqrt(variancia))
    u = stats.mannwhitneyu(b, a, alternative="two-sided").statistic
    correcao = 0.5
    return ReferenciaH0(
        distribuicao,
        centro,
        float(distribuicao.ppf(1 - alpha / 2) - centro),
        max(abs(float(u) - centro) - correcao, 0.0),
        correcao,
    )


def referencias_h0(a: np.ndarray, b: np.ndarray, alpha: float = ALPHA) -> dict[str, ReferenciaH0]:
    return {
        TESTE_PARAMETRICO: referencia_welch(a, b, alpha),
        TESTE_NAO_PARAMETRICO: referencia_mann_whitney(a, b, alpha),
    }


def estatisticas_sob_h0(
    n: int,
    situacao: str,
    n_simulacoes: int,
    rng: np.random.Generator,
) -> dict[str, pd.DataFrame]:
    """Estatística e p-valor de cada teste em conjuntos simulados com efeito zero."""
    conjuntos = [gerar_conjunto(n, 0, situacao, rng) for _ in range(n_simulacoes)]
    a, b = (np.array(grupo) for grupo in zip(*conjuntos))
    welch = stats.ttest_ind(b, a, axis=1, equal_var=False, alternative="two-sided")
    mann_whitney = stats.mannwhitneyu(b, a, axis=1, alternative="two-sided")
    return {
        TESTE_PARAMETRICO: pd.DataFrame({"estatistica": welch.statistic, "p_valor": welch.pvalue}),
        TESTE_NAO_PARAMETRICO: pd.DataFrame({"estatistica": mann_whitney.statistic, "p_valor": mann_whitney.pvalue}),
    }


def conjunto_exemplo() -> tuple[np.ndarray, np.ndarray]:
    return gerar_conjunto(N_EXEMPLO, EFEITO_EXEMPLO, SITUACAO_EXEMPLO, get_rng())


def interpretar(teste: str, r: pd.Series, alpha: float = ALPHA) -> str:
    decisao = "rejeita H₀" if r["rejeita_h0"] else "não rejeita H₀"
    return (
        f"{teste}: p = {r['p_valor']:.4f}, {decisao} a α = {alpha}; "
        f"{r['medida_efeito']} = {r['efeito']:.2f}"
    )


def main() -> None:
    sem_bot, com_bot = conjunto_exemplo()
    resultados = aplicar_testes(sem_bot, com_bot)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    resultados.to_csv(ARQUIVO_EXEMPLO)
    print(f"Situação: {SITUACAO_EXEMPLO} | n = {N_EXEMPLO} por grupo | efeito = {EFEITO_EXEMPLO}")
    print(f"Médias: sem bot {sem_bot.mean():.2f} h, com bot {com_bot.mean():.2f} h")
    print(f"Medianas: sem bot {np.median(sem_bot):.2f} h, com bot {np.median(com_bot):.2f} h")
    for teste, r in resultados.iterrows():
        print(interpretar(teste, r))


if __name__ == "__main__":
    main()
