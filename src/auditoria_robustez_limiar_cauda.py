from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path("outputs/reports/galaxias_tamanho")
df = pd.read_csv(BASE / "dados.csv")

cols = ["ra", "dec", "z", "modelMag_r"]
df = df[cols].apply(pd.to_numeric, errors="coerce")
df = df.replace([np.inf, -np.inf], np.nan).dropna()

# Mesmas cinco faixas de redshift do teste anterior.
df["faixa_z"] = pd.cut(
    df["z"], bins=np.linspace(0.05, 0.10, 6), include_lowest=True
)

ra_edges = np.linspace(df["ra"].min(), df["ra"].max(), 5)
dec_edges = np.linspace(df["dec"].min(), df["dec"].max(), 4)

ra_bin = pd.cut(df["ra"], ra_edges, labels=False, include_lowest=True)
dec_bin = pd.cut(df["dec"], dec_edges, labels=False, include_lowest=True)
df["celula"] = dec_bin * 4 + ra_bin
df = df.dropna(subset=["faixa_z", "celula"]).copy()

print("=== ROBUSTEZ POR LIMIAR DE MAGNITUDE ===")
print("A amplitude é a maior taxa menos a menor taxa entre as 12 células.")
print("Os resultados são descritivos, sem p-valores nesta etapa.\n")

resultados = []

for limite in [18, 18.5, 19, 19.5, 20, 21, 22]:
    cauda = (df["modelMag_r"] > limite).astype(int)
    tabela = pd.DataFrame({
        "celula": df["celula"].astype(int),
        "cauda": cauda,
    }).groupby("celula")["cauda"].agg(["sum", "count"])

    taxas = tabela["sum"] / tabela["count"]
    amplitude = taxas.max() - taxas.min()

    resultados.append({
        "limiar": limite,
        "N_cauda": int(cauda.sum()),
        "pct_catalogo": 100 * cauda.mean(),
        "menor_taxa_pct": 100 * taxas.min(),
        "maior_taxa_pct": 100 * taxas.max(),
        "amplitude_pp": 100 * amplitude,
        "celula_max": int(taxas.idxmax()),
        "celula_min": int(taxas.idxmin()),
    })

res = pd.DataFrame(resultados)
print(res.to_string(
    index=False,
    formatters={
        "pct_catalogo": "{:.3f}".format,
        "menor_taxa_pct": "{:.3f}".format,
        "maior_taxa_pct": "{:.3f}".format,
        "amplitude_pp": "{:.3f}".format,
    }
))

out = BASE / "auditoria_robustez_limiar_cauda"
out.mkdir(parents=True, exist_ok=True)
res.to_csv(out / "resultados.csv", index=False)
print(f"\nRelatório salvo em: {out / 'resultados.csv'}")
print("A robustez dos p-valores ainda precisa ser testada separadamente.")
