# Dados reais: tempo até o merge de PRs

## Fonte

- **Repositório:** [TryGhost/Ghost](https://github.com/TryGhost/Ghost) (GitHub, público)
- **Bot de revisão:** [CodeRabbit](https://coderabbit.ai) (`coderabbitai`), que comenta e revisa PRs automaticamente
- **Coleta:** API GraphQL do GitHub, via `gh api graphql`, em 02/11/2026
- **Script:** [`src/coleta.py`](../../src/coleta.py) (`python -m src.coleta`, requer `gh auth login`)

## Critérios

| | `sem_bot` | `com_bot` |
|---|---|---|
| PRs criados em | out/2024 e nov/2024 | fev/2025 e mar/2025 |
| Condição | o CodeRabbit **não** comentou nem revisou | o CodeRabbit comentou ou revisou |
| PRs elegíveis | 410 | 435 |
| Amostra | 30 | 30 |

- **Adoção do bot** (PRs de humanos mergeados):

  | Mês | ago/24 | set/24 | nov/24 | dez/24 | jan/25 | fev/25 | abr/25 |
  |---|---|---|---|---|---|---|---|
  | Com CodeRabbit | 0/110 | 0/183 | 2/194 | 8/117 | ~55/84 | 139/139 | 238/239 |

  **Dez/2024 e jan/2025 foram excluídos** por serem a transição. As janelas são as mais
  próximas possíveis da virada, para reduzir outras mudanças no projeto entre os períodos.
- **Exclusões:** PRs não mergeados e PRs abertos por bots (Renovate, Dependabot etc.).
  Outliers foram **mantidos**: eles fazem parte do fenômeno.
- **Amostragem:** 30 PRs sorteados por grupo entre os elegíveis, com `numpy.random.default_rng(42)`.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `prs_elegiveis.csv` | Todos os PRs que atendem aos critérios (população) |
| `prs_merge.csv` | Amostra usada no laboratório (30 por grupo) |

Colunas: `numero`, `url`, `autor`, `created_at`, `merged_at` (UTC, ISO 8601), `grupo`,
`horas_ate_merge` (`merged_at − created_at`, em horas).

## Limitações

- **Comparação antes × depois:** além do bot, outras coisas podem ter mudado entre os períodos
  (equipe, fase do projeto, sazonalidade). A diferença não pode ser atribuída só ao bot.
- O Ghost é mantido por uma equipe interna que costuma mergear os próprios PRs em minutos;
  o resultado vale para esse fluxo de trabalho, não para projetos dependentes de revisores externos.
- O tempo conta desde a criação do PR, inclusive o período em rascunho (*draft*).
