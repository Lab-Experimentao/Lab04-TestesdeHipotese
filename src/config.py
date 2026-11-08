"""Configurações globais do laboratório: semente, parâmetros da simulação, cores e links."""

from pathlib import Path

import numpy as np

# Reprodutibilidade: toda aleatoriedade do projeto deve vir de get_rng().
SEED = 42

# Parâmetros da simulação (seção 2.d do enunciado)
ALPHA = 0.05
ALPHA_ESTRITO = 0.01          # só para comparar com ALPHA (pergunta 12 da apresentação)
N_SIMULACOES = 10_000
# Deslocamento de com_bot no log, em desvios. O início é mais fino porque o efeito observado nos
# dados reais é pequeno (de -0,16 nos elegíveis a +0,26 na amostra)
EFEITOS = (0, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2)

# Caminhos
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Links exibidos no topo do dashboard
DASHBOARD_URL = "https://<preencher-apos-publicar>.streamlit.app"
PROJECTS_URL = "https://github.com/orgs/Lab-Experimentao/projects/3/views/1"
REPO_URL = "https://github.com/Lab-Experimentao/Lab04-TestesdeHipotese"

# Par de testes escolhido pelo grupo: P1
TESTE_PARAMETRICO = "t de Welch"
TESTE_NAO_PARAMETRICO = "Mann-Whitney"

# Grupos comparados, na ordem em que aparecem no dashboard
NOMES_GRUPOS = {"sem_bot": "Sem bot", "com_bot": "Com bot"}

# Paleta fixa por teste: a mesma cor em todos os gráficos (G1 a G4)
CORES_TESTES = {
    TESTE_PARAMETRICO: "#2563EB",      # azul
    TESTE_NAO_PARAMETRICO: "#EA580C",  # laranja
}

# Cores auxiliares
COR_REAL = "#52525B"          # dados reais (G1)
COR_SIMULADO = "#A1A1AA"      # dados simulados (G1)
COR_REJEICAO = "#BE185D"      # região de rejeição (G2); um vermelho se confundiria com o laranja do Mann-Whitney
COR_REFERENCIA = "#111113"    # linha de 5% (G3)


def get_rng(seed: int | np.random.SeedSequence = SEED) -> np.random.Generator:
    """Retorna um gerador NumPy com semente fixa."""
    return np.random.default_rng(seed)
