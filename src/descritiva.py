"""Análise descritiva dos dados reais: tempo até o merge (horas) por grupo.

Execute com: python -m src.descritiva
"""

import numpy as np
import pandas as pd
from scipy import stats

from src.config import PROCESSED_DATA_DIR, RAW_DATA_DIR

ARQUIVO_AMOSTRA = RAW_DATA_DIR / "prs_merge.csv"
ARQUIVO_DESCRITIVA = PROCESSED_DATA_DIR / "descritiva.csv"


def carregar_amostra() -> pd.DataFrame:
    return pd.read_csv(ARQUIVO_AMOSTRA)


def outliers_iqr(x: pd.Series) -> pd.Series:
    """Marca como outlier o que fica fora de [Q1 - 1,5·IQR, Q3 + 1,5·IQR]."""
    q1, q3 = x.quantile([0.25, 0.75])
    iqr = q3 - q1
    return (x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)


def resumo(x: pd.Series) -> dict:
    log_x = np.log(x)
    outliers = outliers_iqr(x)
    return {
        "n": len(x),
        "media_h": x.mean(),
        "mediana_h": x.median(),
        "desvio_h": x.std(ddof=1),
        "min_h": x.min(),
        "max_h": x.max(),
        "assimetria": stats.skew(x, bias=False),
        "outliers_n": int(outliers.sum()),
        "outliers_pct": 100 * outliers.mean(),
        # Parâmetros de uma lognormal ajustada: base para a simulação
        "media_log": log_x.mean(),
        "desvio_log": log_x.std(ddof=1),
        "assimetria_log": stats.skew(log_x, bias=False),
    }


def descritiva(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        grupo: resumo(g["horas_ate_merge"]) for grupo, g in df.groupby("grupo")
    }).T


def main() -> None:
    tabela = descritiva(carregar_amostra())
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    tabela.to_csv(ARQUIVO_DESCRITIVA, index_label="grupo")
    with pd.option_context("display.float_format", "{:.2f}".format, "display.width", 120):
        print(tabela.T)


if __name__ == "__main__":
    main()
