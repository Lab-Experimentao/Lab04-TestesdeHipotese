"""Coleta do tempo até o merge de PRs do TryGhost/Ghost, antes e depois da adoção do CodeRabbit.

Requer o GitHub CLI autenticado (gh auth login). Execute com: python -m src.coleta

Gera:
- data/raw/prs_elegiveis.csv: todos os PRs que atendem aos critérios (população)
- data/raw/prs_merge.csv: amostra aleatória de N_POR_GRUPO PRs por grupo (usada no lab)
"""

import json
import subprocess

import pandas as pd

from src.config import RAW_DATA_DIR, get_rng

REPO = "TryGhost/Ghost"
BOT = "coderabbitai"
N_POR_GRUPO = 30

# Adoção: o bot comenta em 0 a 2 PRs/mês até nov/2024, em ~7% em dez/2024, em ~65% em jan/2025
# e em ~100% a partir de fev/2025. Dez/2024 e jan/2025 ficam de fora (transição); as janelas
# são as mais próximas possíveis da virada, para reduzir outras mudanças entre os períodos.
JANELAS = {
    "sem_bot": ["2024-10", "2024-11"],
    "com_bot": ["2025-02", "2025-03"],
}

QUERY = """
query($q: String!, $after: String) {
  search(query: $q, type: ISSUE, first: 50, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on PullRequest {
        number url createdAt mergedAt
        author { login __typename }
        comments(first: 50) { nodes { author { login } } }
        reviews(first: 50) { nodes { author { login } } }
      }
    }
  }
}
"""


def _graphql(q: str, after: str | None) -> dict:
    args = ["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"q={q}"]
    if after:
        args += ["-f", f"after={after}"]
    saida = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(saida.stdout)["data"]["search"]


def buscar_mes(mes: str) -> list[dict]:
    """Todos os PRs mergeados criados no mês (AAAA-MM)."""
    inicio = pd.Timestamp(f"{mes}-01")
    fim = inicio + pd.offsets.MonthEnd(0)
    q = f"repo:{REPO} is:pr is:merged created:{inicio:%Y-%m-%d}..{fim:%Y-%m-%d}"
    prs, after = [], None
    while True:
        pagina = _graphql(q, after)
        prs += pagina["nodes"]
        if not pagina["pageInfo"]["hasNextPage"]:
            return prs
        after = pagina["pageInfo"]["endCursor"]


def bot_revisou(pr: dict) -> bool:
    autores = [n["author"]["login"] for n in pr["comments"]["nodes"] + pr["reviews"]["nodes"]
               if n["author"]]
    return BOT in autores


def coletar() -> pd.DataFrame:
    linhas = []
    for grupo, meses in JANELAS.items():
        for mes in meses:
            for pr in buscar_mes(mes):
                # Exclui PRs abertos por bots (Dependabot, Renovate...) e de contas apagadas
                if not pr["author"] or pr["author"]["__typename"] == "Bot":
                    continue
                # O grupo precisa refletir o tratamento de fato recebido pelo PR
                if bot_revisou(pr) != (grupo == "com_bot"):
                    continue
                linhas.append({
                    "numero": pr["number"],
                    "url": pr["url"],
                    "autor": pr["author"]["login"],
                    "created_at": pr["createdAt"],
                    "merged_at": pr["mergedAt"],
                    "grupo": grupo,
                })
    df = pd.DataFrame(linhas)
    criado = pd.to_datetime(df["created_at"])
    mergeado = pd.to_datetime(df["merged_at"])
    df["horas_ate_merge"] = ((mergeado - criado).dt.total_seconds() / 3600).round(2)
    return df.sort_values(["grupo", "numero"]).reset_index(drop=True)


def amostrar(elegiveis: pd.DataFrame) -> pd.DataFrame:
    rng = get_rng()
    partes = [
        g.iloc[rng.choice(len(g), size=N_POR_GRUPO, replace=False)]
        for _, g in elegiveis.groupby("grupo")
    ]
    return pd.concat(partes).sort_values(["grupo", "numero"]).reset_index(drop=True)


def main() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    elegiveis = coletar()
    elegiveis.to_csv(RAW_DATA_DIR / "prs_elegiveis.csv", index=False)
    amostra = amostrar(elegiveis)
    amostra.to_csv(RAW_DATA_DIR / "prs_merge.csv", index=False)
    print("PRs elegíveis por grupo:", elegiveis["grupo"].value_counts().to_dict())
    print("Amostra por grupo:", amostra["grupo"].value_counts().to_dict())


if __name__ == "__main__":
    main()
