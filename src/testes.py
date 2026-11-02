"""Os dois testes do par P1, com estatística, p-valor e tamanho do efeito.

Ambos são bicaudais (seção 1 do dashboard) e tratam o primeiro grupo como referência: um
efeito positivo indica valores maiores no segundo grupo.

Execute com: python -m src.testes
"""

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


def interpretar(teste: str, r: pd.Series, alpha: float = ALPHA) -> str:
    decisao = "rejeita H₀" if r["rejeita_h0"] else "não rejeita H₀"
    return (
        f"{teste}: p = {r['p_valor']:.4f}, {decisao} a α = {alpha}; "
        f"{r['medida_efeito']} = {r['efeito']:.2f}"
    )


def main() -> None:
    sem_bot, com_bot = gerar_conjunto(N_EXEMPLO, EFEITO_EXEMPLO, SITUACAO_EXEMPLO, get_rng())
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
