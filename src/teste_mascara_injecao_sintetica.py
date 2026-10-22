#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Injeção sintética através da máscara real do SDSS.

Objetivo: verificar se o detector (FFT + Hann + P(k=3)) recupera um sinal
A=0.10, λ=100 Mpc em catálogos com a MESMA máscara RA×Dec e o MESMO n(z)
do SDSS real (100k). NÃO analisa dados reais.

Saídas em outputs/reports/mascara_injecao_sintetica/:
    resultados.csv
    comparacao_A0_vs_A010.png
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from astropy.cosmology import FlatLambdaCDM
from pathlib import Path

# ---------------- Configuração ----------------
CATALOGO     = "data/raw/galaxias_massa_z006_z008_100k.csv"
OUTPUT_DIR   = Path("outputs/reports/mascara_injecao_sintetica")
REPS         = 200
WAVELENGTH   = 100.0
AMPLITUDES   = (0.0, 0.10)
GRID         = 64
BOX          = 660.0
N_TARGET     = 100_000
SEED_MASTER  = 20261022
COSMO        = FlatLambdaCDM(H0=70, Om0=0.3)

N_RA_BINS, N_DEC_BINS, N_Z_BINS = 72, 36, 50
AXES = ("x", "y", "z")
AXIS_NAMES = {0: "x", 1: "y", 2: "z"}

# ---------------- Passo 1: ler máscara real ----------------
print("[INFO] Lendo catálogo real para extrair máscara...")
df = pd.read_csv(CATALOGO, comment="#")
print(f"[INFO] N real = {len(df)}")
print(f"[INFO] RA:  [{df.ra.min():.1f}, {df.ra.max():.1f}]")
print(f"[INFO] Dec: [{df.dec.min():.1f}, {df.dec.max():.1f}]")
print(f"[INFO] z:   [{df.z.min():.4f}, {df.z.max():.4f}]")

hist_radec, ra_edges, dec_edges = np.histogram2d(
    df.ra, df.dec, bins=(N_RA_BINS, N_DEC_BINS)
)
p_radec = hist_radec.flatten() / hist_radec.sum()
n_active = int((hist_radec > 0).sum())
print(f"[INFO] Máscara {N_RA_BINS}x{N_DEC_BINS} com {n_active} bins ativos")

hist_z, z_edges = np.histogram(df.z, bins=N_Z_BINS)
p_z = hist_z / hist_z.sum()

# ---------------- Passo 2: funções ----------------
def sample_from_mask(rng, n):
    idx = rng.choice(len(p_radec), size=n, p=p_radec)
    ra_i = idx // N_DEC_BINS
    dec_i = idx % N_DEC_BINS
    ra  = rng.uniform(ra_edges[ra_i],  ra_edges[ra_i + 1])
    dec = rng.uniform(dec_edges[dec_i], dec_edges[dec_i + 1])
    z_i = rng.choice(len(p_z), size=n, p=p_z)
    z   = rng.uniform(z_edges[z_i],  z_edges[z_i + 1])
    return ra, dec, z


def radec_z_to_cart(ra, dec, z):
    d = COSMO.comoving_distance(z).value
    ra_r  = np.radians(ra)
    dec_r = np.radians(dec)
    x = d * np.cos(dec_r) * np.cos(ra_r)
    y = d * np.cos(dec_r) * np.sin(ra_r)
    zc = d * np.sin(dec_r)
    return x, y, zc


def gerar_catalogo_modulado(rng, n_target, A, axis):
    """Rejection sampling até preencher n_target (N fixo)."""
    pts = []
    filled = 0
    while filled < n_target:
        batch = max(4096, 2 * (n_target - filled))
        ra, dec, z = sample_from_mask(rng, batch)
        x, y, zc = radec_z_to_cart(ra, dec, z)
        coords = np.column_stack([x, y, zc]) + BOX / 2.0
        if A > 0:
            prob = (1.0 + A * np.cos(2 * np.pi * coords[:, axis] / WAVELENGTH)) / (1 + A)
            keep = rng.random(len(prob)) < prob
            coords = coords[keep]
        pts.append(coords)
        filled += len(coords)
    return np.vstack(pts)[:n_target]


def medir_P_k3(coords, axis):
    hist, _ = np.histogramdd(
        coords, bins=(GRID, GRID, GRID),
        range=((0, BOX), (0, BOX), (0, BOX)),
    )
    field = hist.astype(np.float64) - hist.mean()
    win = np.hanning(GRID)
    window = win[:, None, None] * win[None, :, None] * win[None, None, :]
    field *= window
    power = np.abs(np.fft.fftn(field)) ** 2
    freq = np.fft.fftfreq(GRID, d=BOX / GRID) * 2 * np.pi
    kt = 2 * np.pi / WAVELENGTH
    ip = int(np.argmin(np.abs(freq - kt)))
    ineg = int(np.argmin(np.abs(freq + kt)))
    if axis == 0:
        return float(0.5 * (power[ip, 0, 0] + power[ineg, 0, 0]))
    if axis == 1:
        return float(0.5 * (power[0, ip, 0] + power[0, ineg, 0]))
    return float(0.5 * (power[0, 0, ip] + power[0, 0, ineg]))

# ---------------- Passo 3: loop ----------------
rng_master = np.random.default_rng(SEED_MASTER)
rows = []
for A in AMPLITUDES:
    for rep in range(REPS):
        seed = int(rng_master.integers(0, 2**32 - 1))
        rng = np.random.default_rng(seed)
        for axis in (0, 1, 2):
            coords = gerar_catalogo_modulado(rng, N_TARGET, A, axis)
            P = medir_P_k3(coords, axis)
            rows.append({
                "amplitude": A, "rep": rep, "seed": seed,
                "axis": AXIS_NAMES[axis], "P": P, "N_kept": len(coords),
            })
        if (rep + 1) % 25 == 0:
            print(f"  A={A:.2f}  rep {rep+1}/{REPS}")

dfout = pd.DataFrame(rows)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
dfout.to_csv(OUTPUT_DIR / "resultados.csv", index=False)
print(f"\n[+] CSV: {OUTPUT_DIR / 'resultados.csv'}")

# ---------------- Passo 4: análise ----------------
print("\n=== RESUMO POR EIXO ===")
summary = []
for axname in AXES:
    P0 = dfout[(dfout.amplitude == 0.0)  & (dfout.axis == axname)]["P"].values
    P1 = dfout[(dfout.amplitude == 0.10) & (dfout.axis == axname)]["P"].values
    mw = stats.mannwhitneyu(P0, P1, alternative="two-sided")
    auc_val = mw.statistic / (len(P0) * len(P1))
    med0, med1 = float(np.median(P0)), float(np.median(P1))
    mean0, mean1 = float(P0.mean()), float(P1.mean())
    row = {
        "axis": axname,
        "med_A0": med0, "med_A010": med1, "ratio_med": med1 / med0 if med0 else float("nan"),
        "mean_A0": mean0, "mean_A010": mean1,
        "auc": auc_val, "p_mw": float(mw.pvalue),
    }
    summary.append(row)
    print(f"\nEixo {axname}:")
    print(f"  A=0    → mediana={med0:8.2f}   média={mean0:8.2f}")
    print(f"  A=0.10 → mediana={med1:8.2f}   média={mean1:8.2f}")
    print(f"  razão medianas = {row['ratio_med']:.2f}")
    print(f"  AUC = {auc_val:.3f}   p_MW = {mw.pvalue:.3e}")

pd.DataFrame(summary).to_csv(OUTPUT_DIR / "resumo_por_eixo.csv", index=False)

# ---------------- Passo 5: gráfico ----------------
fig, axes_plt = plt.subplots(1, 3, figsize=(15, 4))
for ax_plt, axname in zip(axes_plt, AXES):
    P0 = dfout[(dfout.amplitude == 0.0)  & (dfout.axis == axname)]["P"].values
    P1 = dfout[(dfout.amplitude == 0.10) & (dfout.axis == axname)]["P"].values
    ax_plt.hist(P0, bins=30, alpha=0.5, label="A=0",    color="gray")
    ax_plt.hist(P1, bins=30, alpha=0.5, label="A=0.10", color="red")
    ax_plt.set_xlabel(f"P(k=3) eixo {axname}")
    ax_plt.set_ylabel("contagem")
    ax_plt.set_title(f"Máscara SDSS real — eixo {axname}")
    ax_plt.legend()
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "comparacao_A0_vs_A010.png", dpi=140)
plt.close(fig)
print(f"\n[+] Gráfico: {OUTPUT_DIR / 'comparacao_A0_vs_A010.png'}")

# ---------------- Sanidade ----------------
print("\n[CHECK] N_kept único (deve ser 100000):",
      dfout["N_kept"].unique().tolist())