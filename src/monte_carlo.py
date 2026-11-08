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
    TESTE_NAO_PARAMETRICO,
    get_rng,
)
from src.simulacao import SITUACOES, calibrar, gerar_lote
from src.testes import testes_em_lote

ARQUIVO_SIMULACOES = PROCESSED_DATA_DIR / "simulacoes.csv"

# Quantil da normal para a margem de erro de 95% da proporção estimada
Z_95 = 1.96
# Taxa aceitável, em múltiplos de α: critério liberal de Bradley (1978), "Robustness?"
FAIXA_ACEITAVEL = (0.5, 1.5)
# Acima desta parcela das rejeições numa só direção, o erro não está dividido entre as caudas
LIMITE_UMA_DIRECAO = 0.75


def rng_da_configuracao(situacao: str, efeito: float) -> np.random.Generator:
    # crc32 em vez de hash(): o hash de textos muda a cada execução do Python
    return get_rng(np.random.SeedSequence([SEED, zlib.crc32(situacao.encode()), round(efeito * 1000)]))


def gerar_lote_da_configuracao(
    situacao: str,
    efeito: float,
    n_simulacoes: int = N_SIMULACOES,
) -> tuple[np.ndarray, np.ndarray]:
    return gerar_lote(
        n_simulacoes,
        SITUACOES[situacao].n,
        efeito,
        situacao,
        rng_da_configuracao(situacao, efeito),
    )


def simular_configuracao(
    situacao: str,
    efeito: float,
    n_simulacoes: int = N_SIMULACOES,
) -> pd.DataFrame:
    """Uma linha por teste e por α, com as rejeições em n_simulacoes conjuntos."""
    sem_bot, com_bot = gerar_lote_da_configuracao(situacao, efeito, n_simulacoes)
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


def salvar_simulacoes() -> pd.DataFrame:
    resultados = simular_tudo()
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    resultados.to_csv(ARQUIVO_SIMULACOES, index=False, float_format="%.6g")
    return resultados


def carregar_simulacoes() -> pd.DataFrame:
    """Lê o CSV, gerando-o antes se não existir: o dashboard abre com um único comando."""
    if not ARQUIVO_SIMULACOES.exists():
        salvar_simulacoes()
    return pd.read_csv(ARQUIVO_SIMULACOES)


def _diagnostico(linha: pd.Series, alpha: float) -> str:
    if not linha["h0_verdadeira"]:
        return "Não se aplica"
    if linha["proporcao"] < FAIXA_ACEITAVEL[0] * alpha:
        return "Conservador"
    if linha["proporcao"] > FAIXA_ACEITAVEL[1] * alpha:
        return "Liberal"
    diagnostico = f"Perto de {100 * alpha:g}%"
    parcela = max(linha["rejeicoes_com_bot_maior"], linha["rejeicoes"] - linha["rejeicoes_com_bot_maior"])
    parcela /= linha["rejeicoes"]
    if parcela > LIMITE_UMA_DIRECAO:
        diagnostico += f", mas {100 * parcela:.0f}% numa só direção"
    return diagnostico


def erro_tipo_1(simulacoes: pd.DataFrame, alpha: float = ALPHA) -> pd.DataFrame:
    """Linhas com efeito zero, uma por situação × teste, com o diagnóstico de cada taxa.

    h0_verdadeira indica se a taxa mede mesmo erro tipo I: em variancias_diferentes, com efeito
    zero, só o H₀ do Mann-Whitney é verdadeiro.
    """
    linhas = simulacoes[(simulacoes["efeito"] == 0) & (simulacoes["alpha"] == alpha)].copy()
    linhas["h0_verdadeira"] = [
        SITUACOES[situacao].mede_erro_tipo_1 or teste == TESTE_NAO_PARAMETRICO
        for situacao, teste in zip(linhas["situacao"], linhas["teste"])
    ]
    linhas["diagnostico"] = linhas.apply(_diagnostico, axis=1, alpha=alpha)
    return linhas


def main() -> None:
    resultados = salvar_simulacoes()

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
