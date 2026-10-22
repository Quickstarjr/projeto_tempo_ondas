from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261022
N_PERM = 10000

BASE = Path("outputs/reports/galaxias_tamanho")
df = pd.read_csv(BASE / "dados.csv")
cols = ["ra", "dec", "z", "modelMag_r"]
df = df[cols].apply(pd.to_numeric, errors="coerce")
df = df.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)

df["cauda"] = (df["modelMag_r"] > 19).astype(int)
df["faixa_z"] = pd.cut(
    df["z"], bins=np.linspace(0.05, 0.10, 6), include_lowest=True
)

# Mesma grade angular 4 x 3 usada na auditoria anterior.
ra_edges = np.linspace(df["ra"].min(), df["ra"].max(), 5)
dec_edges = np.linspace(df["dec"].min(), df["dec"].max(), 4)

ra_bin = pd.cut(df["ra"], ra_edges, labels=False, include_lowest=True)
dec_bin = pd.cut(df["dec"], dec_edges, labels=False, include_lowest=True)
df["celula"] = dec_bin * 4 + ra_bin

# Considera somente objetos que entraram nas cinco faixas de redshift.
df = df.dropna(subset=["faixa_z", "celula"]).copy()
df["celula"] = df["celula"].astype(int)

celulas = np.sort(df["celula"].unique())
codigos = {c: i for i, c in enumerate(celulas)}
cell = df["celula"].map(codigos).to_numpy()
n_cells = len(celulas)
y = df["cauda"].to_numpy()
strata = df["faixa_z"].cat.codes.to_numpy()

# Estatística: amplitude entre a maior e a menor taxa por célula.
def estatistica(labels):
    total = np.bincount(cell, minlength=n_cells)
    cauda = np.bincount(cell, weights=labels, minlength=n_cells)
    taxas = cauda / total
    return float(taxas.max() - taxas.min()), taxas, total, cauda

obs, taxas_obs, total, cauda_obs = estatistica(y)

# Permuta rótulos dentro de cada faixa de redshift:
# preserva a quantidade de cauda em cada faixa.
rng = np.random.default_rng(SEED)
indices_por_faixa = [
    np.flatnonzero(strata == s)
    for s in np.unique(strata) if s >= 0
]
simulados = np.empty(N_PERM)

for i in range(N_PERM):
    yp = y.copy()
    for idx in indices_por_faixa:
        yp[idx] = rng.permutation(yp[idx])
    simulados[i] = estatistica(yp)[0]

p_perm = (1 + np.count_nonzero(simulados >= obs)) / (N_PERM + 1)

print("=" * 68)
print("PERMUTAÇÃO DA CAUDA CONTROLADA POR FAIXA DE REDSHIFT")
print("=" * 68)
print(f"Objetos analisados: {len(df)}")
print(f"Objetos na cauda: {int(y.sum())}")
print(f"Células angulares ocupadas: {n_cells}")
print(f"Permutações: {N_PERM}")
print(f"Amplitude observada das taxas: {100*obs:.3f} pontos percentuais")
print(
    "Amplitude simulada (mediana; P95; P99): "
    f"{100*np.median(simulados):.3f}; "
    f"{100*np.quantile(simulados, .95):.3f}; "
    f"{100*np.quantile(simulados, .99):.3f} pp"
)
print(f"p de permutação (unilateral): {p_perm:.5f}")

print("\n=== TAXA OBSERVADA POR CÉLULA ===")
for c, rate, n, k in zip(celulas, taxas_obs, total, cauda_obs):
    print(
        f"célula {c:2d}: cauda={int(k):3d}/{int(n):4d} "
        f"({100*rate:5.2f}%)"
    )

out = BASE / "auditoria_permutacao_cauda"
out.mkdir(parents=True, exist_ok=True)
pd.DataFrame({"amplitude_taxas": simulados}).to_csv(
    out / "distribuicao_permutacoes.csv", index=False
)
print(f"\nDistribuição nula salva em: {out}")
print("Interpretação limitada à grade e ao controle por redshift.")
