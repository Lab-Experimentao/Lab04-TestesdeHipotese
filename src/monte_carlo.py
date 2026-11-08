"""Motor Monte Carlo: proporção de rejeições de cada teste por situação × tamanho do efeito.

Com efeito zero, a proporção estima o erro tipo I (Q1); com efeito, o poder (Q2). As situações de
violação respondem à Q3. Cada configuração tem a própria semente, derivada do seu nome e efeito:
incluir uma situação ou um efeito não altera os resultados das demais.

Execute com: python -m src.monte_carlo
"""

import zlib

import numpy as np
import pandas as pd

from src.config import (
    ALPHA,
    ALPHA_ESTRITO,
    EFEITOS,
    N_SIMULACOES,
    PROCESSED_DATA_DIR,
    SEED,
    get_rng,
)
from src.simulacao import SITUACOES, calibrar, gerar_lote
from src.testes import testes_em_lote

ARQUIVO_SIMULACOES = PROCESSED_DATA_DIR / "simulacoes.csv"

# Quantil da normal para a margem de erro de 95% da proporção estimada
Z_95 = 1.96


def rng_da_configuracao(situacao: str, efeito: float) -> np.random.Generator:
    # crc32 em vez de hash(): o hash de textos muda a cada execução do Python
    return get_rng(np.random.SeedSequence([SEED, zlib.crc32(situacao.encode()), round(efeito * 1000)]))


def simular_configuracao(
    situacao: str,
    efeito: float,
    n_simulacoes: int = N_SIMULACOES,
) -> pd.DataFrame:
    """Uma linha por teste e por α, com as rejeições em n_simulacoes conjuntos."""
    sem_bot, com_bot = gerar_lote(
        n_simulacoes,
        SITUACOES[situacao].n,
        efeito,
        situacao,
        rng_da_configuracao(situacao, efeito),
    )
    linhas = []
    for teste, resultado in testes_em_lote(sem_bot, com_bot).items():
        for alpha in (ALPHA, ALPHA_ESTRITO):
            rejeita = resultado["p_valor"] < alpha
            proporcao = rejeita.mean()
            linhas.append({
                "situacao": situacao,
                "n_sem_bot": sem_bot.shape[1],
                "n_com_bot": com_bot.shape[1],
                "efeito": efeito,
                "multiplicador": np.exp(efeito * calibrar().sigma),
                "teste": teste,
                "alpha": alpha,
                "n_simulacoes": n_simulacoes,
                "rejeicoes": int(rejeita.sum()),
                # Separa as direções: sob H₀, um teste simétrico divide as rejeições ao meio
                "rejeicoes_com_bot_maior": int((rejeita & resultado["segundo_maior"]).sum()),
                "proporcao": proporcao,
                "margem_erro": Z_95 * np.sqrt(proporcao * (1 - proporcao) / n_simulacoes),
            })
    return pd.DataFrame(linhas)


def simular_tudo(n_simulacoes: int = N_SIMULACOES) -> pd.DataFrame:
    return pd.concat(
        [simular_configuracao(s, e, n_simulacoes) for s in SITUACOES for e in EFEITOS],
        ignore_index=True,
    )


def main() -> None:
    resultados = simular_tudo()
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    resultados.to_csv(ARQUIVO_SIMULACOES, index=False, float_format="%.6g")

    principal = resultados[resultados["alpha"] == ALPHA]
    with pd.option_context("display.width", 120, "display.float_format", "{:.1f}".format):
        print(f"{len(SITUACOES)} situações × {len(EFEITOS)} efeitos, {N_SIMULACOES} repetições, α = {ALPHA}")
        print("Rejeições (%):")
        print(100 * principal.pivot_table(
            index=["situacao", "teste"],
            columns="efeito",
            values="proporcao",
            sort=False,
        ).rename(columns=str))


if __name__ == "__main__":
    main()
