#!/usr/bin/env python3
"""Gera um lote nulo rastreável usando as funções do pipeline original."""

import json
import numpy as np
import pandas as pd
from pathlib import Path

from auditoria_amplitude_espectro import (
    N_PARTICLES, BOX, GRID, WAVELENGTH, AXIS, K_SPECTRUM,
    gerar_catalogo_modulado, espectro_no_eixo,
)

N_CONTROLES = 200
AMPLITUDE = 0.0
SEED_MASTER_CONTROLE = 888

OUT_DIR = Path("outputs/auditoria")
OUT_DIR.mkdir(parents=True, exist_ok=True)

rng_master = np.random.default_rng(SEED_MASTER_CONTROLE)
rows = []

for rep in range(N_CONTROLES):
    seed = int(rng_master.integers(0, 2**32 - 1))
    rng = np.random.default_rng(seed)

    pts = gerar_catalogo_modulado(
        N_PARTICLES, BOX, WAVELENGTH, AMPLITUDE, rng, axis=AXIS
    )
    diag = espectro_no_eixo(pts, BOX, GRID, axis=AXIS)

    row = {
        "seed": seed,
        "rep": rep,
        "amplitude": AMPLITUDE,
        "N_realizado": diag["N_realizado"],
        "pos_idx": diag["pos_idx"],
        "neg_idx": diag["neg_idx"],
        "conjugado": diag["conjugado"],
        "P_pos_k3": diag["P_pos"],
        "P_neg_k3": diag["P_neg"],
        "P_mean_k3": diag["P_mean"],
        "P_max_k3": diag["P_max"],
    }

    for j, kbin in enumerate(K_SPECTRUM):
        row[f"P_k{kbin}"] = float(diag["P_k"][j])

    rows.append(row)

    if (rep + 1) % 25 == 0:
        print(f"[OK] {rep + 1}/{N_CONTROLES}")

df = pd.DataFrame(rows)

csv_path = OUT_DIR / "controle_nulo_auditavel_seed888.csv"
df.to_csv(csv_path, index=False)

manifest = {
    "seed_master": SEED_MASTER_CONTROLE,
    "n_controles": N_CONTROLES,
    "amplitude": AMPLITUDE,
    "N_PARTICLES": N_PARTICLES,
    "BOX": BOX,
    "GRID": GRID,
    "WAVELENGTH": WAVELENGTH,
    "AXIS": AXIS,
    "K_SPECTRUM": list(K_SPECTRUM),
    "gerador": "auditoria_amplitude_espectro.gerar_catalogo_modulado",
    "estimador": "auditoria_amplitude_espectro.espectro_no_eixo",
}
manifest_path = OUT_DIR / "controle_nulo_auditavel_seed888_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

print("\n=== CONTROLE NULO AUDITÁVEL ===")
print(f"CSV: {csv_path}")
print(f"Manifesto: {manifest_path}")
print(f"Linhas: {len(df)}")
print(f"Seeds únicas: {df['seed'].nunique()}")
print(f"N realizado: {df['N_realizado'].unique().tolist()}")
print(f"Amplitude: {df['amplitude'].unique().tolist()}")
print(f"Conjugação: {int(df['conjugado'].sum())}/{len(df)}")
print("P_pos == P_neg:", np.allclose(
    df["P_pos_k3"], df["P_neg_k3"], rtol=1e-10, atol=0
))
print("P_mean == P_pos:", np.allclose(
    df["P_mean_k3"], df["P_pos_k3"], rtol=1e-10, atol=0
))
print("\nResumo:")
print(df[["P_k3", "P_k6", "P_mean_k3"]].describe())
print("\n[CONCLUÍDO] Nenhum arquivo anterior foi sobrescrito.")
