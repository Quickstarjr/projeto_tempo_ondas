import numpy as np
import pandas as pd

from teste_grade_regular import build_grid

arquivo = "outputs/reports/galaxias_tamanho/dados.csv"
df = pd.read_csv(arquivo)
df = df[["ra", "dec", "z", "modelMag_r"]].replace(
    [np.inf, -np.inf], np.nan
).dropna()

df = df[
    df["ra"].between(0, 360)
    & df["dec"].between(-90, 90)
    & df["z"].between(0.049, 0.10)
].copy()

ra = df["ra"].to_numpy(float)
dec = df["dec"].to_numpy(float)

print("=" * 65)
print("AUDITORIA DA GRADE REGULAR — CATÁLOGO REAL")
print("=" * 65)
print(f"Objetos válidos: {len(df)}")

for ro in [0.0, 0.25, 0.50, 0.75]:
    for do in [0.0, 0.25, 0.50, 0.75]:
        re, de, counts = build_grid(ra, dec, ro, do)

        elegiveis = int(np.sum(counts >= 100))
        print(
            f"RA={ro:.2f} DEC={do:.2f} | "
            f"células={len(counts):2d} | "
            f"ocupadas={np.sum(counts > 0):2d} | "
            f"elegíveis (N>=100)={elegiveis:2d} | "
            f"soma={counts.sum()}"
        )

print("\nAUDITORIA CONCLUÍDA")
