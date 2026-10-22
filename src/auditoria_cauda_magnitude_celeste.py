from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

BASE = Path("outputs/reports/galaxias_tamanho")
ARQUIVO = BASE / "dados.csv"
SAIDA = BASE / "auditoria_cauda_magnitude_celeste"
SAIDA.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(ARQUIVO)
cols = ["ra", "dec", "z", "modelMag_r"]
df = df[cols].apply(pd.to_numeric, errors="coerce")
df = df.replace([np.inf, -np.inf], np.nan).dropna()

df["cauda"] = df["modelMag_r"] > 19
df["faixa_z"] = pd.cut(
    df["z"], bins=np.linspace(0.05, 0.10, 6), include_lowest=True
)

print("=" * 72)
print("AUDITORIA ANGULAR DA CAUDA DE MAGNITUDE")
print("=" * 72)
print(f"Total válido: {len(df)}")
print(f"Cauda (mag > 19): {int(df['cauda'].sum())}")

# Compara a fração da cauda por faixa de redshift.
por_z = df.groupby("faixa_z", observed=True).agg(
    N=("cauda", "size"),
    cauda_N=("cauda", "sum"),
)
por_z["cauda_pct"] = 100 * por_z["cauda_N"] / por_z["N"]

print("\n=== FRAÇÃO DA CAUDA POR REDSHIFT ===")
print(por_z.to_string(float_format=lambda x: f"{x:.3f}"))

# Grade angular 4 x 3: diagnóstico grosseiro, não uma máscara oficial.
ra_edges = np.linspace(df["ra"].min(), df["ra"].max(), 5)
dec_edges = np.linspace(df["dec"].min(), df["dec"].max(), 4)

df["ra_bin"] = pd.cut(df["ra"], ra_edges, include_lowest=True)
df["dec_bin"] = pd.cut(df["dec"], dec_edges, include_lowest=True)

grade_total = pd.crosstab(df["dec_bin"], df["ra_bin"], dropna=False)
grade_cauda = pd.crosstab(
    df.loc[df["cauda"], "dec_bin"],
    df.loc[df["cauda"], "ra_bin"],
    dropna=False,
).reindex(
    index=grade_total.index, columns=grade_total.columns, fill_value=0
)

print("\n=== CONTAGEM TOTAL POR CÉLULA ANGULAR (DEC x RA) ===")
print(grade_total.to_string())

print("\n=== CONTAGEM DA CAUDA (MAG > 19) POR CÉLULA ===")
print(grade_cauda.to_string())

taxa_global = df["cauda"].mean()
taxas = (grade_cauda / grade_total.replace(0, np.nan)).fillna(0)

print("\n=== TAXA DA CAUDA POR CÉLULA (%) ===")
print((100 * taxas).round(2).to_string())
print(f"\nTaxa global da cauda: {100*taxa_global:.3f}%")

# Correlação com coordenadas angulares: apenas triagem exploratória.
print("\n=== SPEARMAN: MAGNITUDE x COORDENADAS ===")
for col in ["ra", "dec"]:
    rho, p = spearmanr(df[col], df["modelMag_r"])
    print(f"{col:>4}: rho={rho:+.4f}, p nominal={p:.5g}")

# Exporta tabelas para inspeção posterior.
por_z.reset_index().to_csv(SAIDA / "cauda_por_redshift.csv", index=False)
grade_total.to_csv(SAIDA / "grade_total.csv")
grade_cauda.to_csv(SAIDA / "grade_cauda.csv")
taxas.to_csv(SAIDA / "taxa_cauda_por_celula.csv")

print(f"\nRelatórios salvos em: {SAIDA}")
print("ATENÇÃO: este teste não comprova estrutura física nem uma onda cósmica.")
