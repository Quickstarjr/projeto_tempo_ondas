from pathlib import Path
import json
import numpy as np
import pandas as pd

BASE = Path("outputs/reports/galaxias_tamanho")
OUT = BASE / "auditoria_permutacao_global_cauda"
DATA = BASE / "dados.csv"

print("=" * 72)
print("AUDITORIA DA PERMUTAÇÃO GLOBAL")
print("=" * 72)

# 1. Verificar os artefatos gerados
for name in ["resumo.json", "maximos_permutados.csv"]:
    path = OUT / name
    print(f"{name}: {'OK' if path.exists() else 'AUSENTE'}")

if not (OUT / "resumo.json").exists():
    raise SystemExit("Execute primeiro o teste de permutação global.")

with open(OUT / "resumo.json", encoding="utf-8") as f:
    resumo = json.load(f)

print("\n[1] RESUMO REGISTRADO")
print(json.dumps(resumo, indent=2, ensure_ascii=False))

# 2. Auditar a distribuição dos máximos
p = OUT / "maximos_permutados.csv"
if p.exists():
    null = pd.read_csv(p)
    col = "max_amplitude"
    if col not in null:
        raise SystemExit(f"Coluna ausente: {col}")

    x = null[col].dropna().to_numpy()
    obs = resumo["observed_global"]["amplitude"]

    print("\n[2] DISTRIBUIÇÃO NULA")
    print(f"Simulações válidas       : {len(x)}")
    print(f"Mínimo                   : {x.min():.6f}")
    print(f"Mediana                  : {np.median(x):.6f}")
    print(f"Média                    : {np.mean(x):.6f}")
    print(f"Desvio-padrão             : {np.std(x, ddof=1):.6f}")
    print(f"Percentil 90             : {np.quantile(x, .90):.6f}")
    print(f"Percentil 95             : {np.quantile(x, .95):.6f}")
    print(f"Percentil 99             : {np.quantile(x, .99):.6f}")
    print(f"Máximo                   : {x.max():.6f}")
    print(f"Máximos >= observado      : {np.sum(x >= obs)}")
    print(f"Proporção empírica        : {np.mean(x >= obs):.6f}")
    print("\nNota: o valor-p com correção +1 é")
    print("(1 + número de máximos >= observado) / (N + 1).")

# 3. Conferir faixas de redshift, magnitudes e células
df = pd.read_csv(DATA)
need = ["ra", "dec", "z", "modelMag_r"]
missing = [c for c in need if c not in df.columns]
if missing:
    raise SystemExit(f"Colunas ausentes nos dados: {missing}")

df = df[need].replace([np.inf, -np.inf], np.nan).dropna()
edges = [0.049, .06, .07, .08, .09, .10]
df["z_bin"] = pd.cut(
    df["z"], bins=edges, right=True, include_lowest=True, labels=False
)
df = df.dropna(subset=["z_bin"]).copy()
df["z_bin"] = df["z_bin"].astype(int)

print("\n[3] DISTRIBUIÇÃO POR REDSHIFT")
print(
    df.groupby("z_bin", observed=True)
      .agg(
          n=("modelMag_r", "size"),
          mag_media=("modelMag_r", "mean"),
          mag_dp=("modelMag_r", "std"),
          mag_min=("modelMag_r", "min"),
          mag_max=("modelMag_r", "max"),
      )
      .to_string(float_format=lambda v: f"{v:.5f}")
)

print("\n[4] CONTAGEM DE CAUDA POR REDSHIFT")
for b, g in df.groupby("z_bin", observed=True):
    row = {"z_bin": int(b), "n": len(g)}
    for t in [18, 18.5, 19, 19.5, 20, 21, 22]:
        row[f"mag_gt_{t:g}"] = int((g["modelMag_r"] > t).sum())
    print(row)

print("\n[5] OCUPAÇÃO DA GRADE ORIGINAL 4 x 3")
ra = df["ra"].to_numpy()
dec = df["dec"].to_numpy()
ra_edges = np.linspace(ra.min(), ra.max(), 5)
dec_edges = np.linspace(dec.min(), dec.max(), 4)
ri = np.clip(np.digitize(ra, ra_edges[1:-1]), 0, 3)
di = np.clip(np.digitize(dec, dec_edges[1:-1]), 0, 2)
cell = di * 4 + ri
counts = np.bincount(cell, minlength=12)
for i, n in enumerate(counts):
    print(f"Célula {i:02d}: {n:4d} objetos")

print("\n[6] LIMITES DA AUDITORIA")
print("- Os CSVs registram máximos, não as magnitudes permutadas.")
print("- A semente permite reproduzir o processo se o código não mudou.")
print("- Para auditar a lógica integralmente, precisamos rever o script.")
print("- A grade 4x3 original não representa a máscara oficial do céu.")
print("\nAuditoria concluída.")
