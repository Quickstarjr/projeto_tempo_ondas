#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoria amplitude × espectro — Projeto Tempo, Ondas e Observador.

Registra P(k) para k=0..12 ao longo do eixo de injeção,
P_pos/P_neg/P_mean/P_max no k=3, e salva UMA LINHA POR REALIZAÇÃO.
NÃO altera verificacao_potencia_gepeto.py.

Uso:
    python src/auditoria_amplitude_espectro.py
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
N_PARTICLES     = 12000
BOX             = 300.0
GRID            = 64
WAVELENGTH      = 100.0
REPS            = 200
AMPLITUDES      = (0.0, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20)
AXIS            = 0
K_SPECTRUM      = tuple(range(0, 13))   # k = 0..12 (índices FFT no eixo de injeção)
SEED_MASTER     = 20261021

OUTPUT_DIR = Path("outputs/reports/auditoria_amplitude_espectro")


# ---------------------------------------------------------------------------
# Geração de catálogo (cópia fiel do original)
# ---------------------------------------------------------------------------
def gerar_catalogo_modulado(n, box, wavelength, amplitude, rng, axis=0):
    if not (0 <= amplitude < 1):
        raise ValueError("Amplitude deve estar em [0, 1).")
    pts = np.empty((n, 3))
    filled = 0
    k = 2 * np.pi / wavelength
    max_dens = 1.0 + amplitude
    while filled < n:
        batch = max(2048, 2 * (n - filled))
        cand = rng.uniform(0, box, size=(batch, 3))
        prob = (1.0 + amplitude * np.cos(k * cand[:, axis])) / max_dens
        keep = rng.random(batch) < prob
        take = cand[keep]
        count = min(len(take), n - filled)
        if count:
            pts[filled:filled + count] = take[:count]
            filled += count
    return pts


# ---------------------------------------------------------------------------
# Espectro ao longo de um eixo
# ---------------------------------------------------------------------------
def espectro_no_eixo(points, box, grid_n, axis=0, k_bins=K_SPECTRUM):
    hist, _ = np.histogramdd(
        points,
        bins=(grid_n, grid_n, grid_n),
        range=((0, box), (0, box), (0, box)),
    )
    field = hist.astype(np.float64) - hist.mean()

    win1 = np.hanning(grid_n)
    window = win1[:, None, None] * win1[None, :, None] * win1[None, None, :]
    field *= window

    ft = np.fft.fftn(field)
    power = np.abs(ft) ** 2

    freq = np.fft.fftfreq(grid_n, d=box / grid_n) * 2 * np.pi
    k_target = 2 * np.pi / WAVELENGTH
    idx_pos = int(np.argmin(np.abs(freq - k_target)))
    idx_neg = int(np.argmin(np.abs(freq + k_target)))

    # P(k) para k=0..12
    P_k = np.empty(len(k_bins), dtype=np.float64)
    for j, kbin in enumerate(k_bins):
        if axis == 0:
            P_k[j] = power[kbin, 0, 0]
        elif axis == 1:
            P_k[j] = power[0, kbin, 0]
        else:
            P_k[j] = power[0, 0, kbin]

    # P_pos / P_neg no k_target
    if axis == 0:
        p_pos = power[idx_pos, 0, 0]; p_neg = power[idx_neg, 0, 0]
    elif axis == 1:
        p_pos = power[0, idx_pos, 0]; p_neg = power[0, idx_neg, 0]
    else:
        p_pos = power[0, 0, idx_pos]; p_neg = power[0, 0, idx_neg]

    return {
        "P_k": P_k,
        "P_pos": float(p_pos),
        "P_neg": float(p_neg),
        "P_mean": float(0.5 * (p_pos + p_neg)),
        "P_max": float(max(p_pos, p_neg)),
        "pos_idx": idx_pos,
        "neg_idx": idx_neg,
        "conjugado": bool(((idx_pos + idx_neg) % grid_n) == 0),
        "N_realizado": len(points),
    }


# ---------------------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------------------
def rodar_experimento():
    rng_master = np.random.default_rng(SEED_MASTER)
    rows = []
    total = len(AMPLITUDES) * REPS
    print(f"[INFO] amplitudes = {AMPLITUDES}")
    print(f"[INFO] reps/amplitude = {REPS}, total = {total}")

    n_done = 0
    for amp in AMPLITUDES:
        for rep in range(REPS):
            seed = int(rng_master.integers(0, 2**32 - 1))
            rng = np.random.default_rng(seed)
            pts = gerar_catalogo_modulado(N_PARTICLES, BOX, WAVELENGTH, amp, rng, axis=AXIS)
            diag = espectro_no_eixo(pts, BOX, GRID, axis=AXIS)

            row = {
                "seed": seed,
                "rep": rep,
                "amplitude": float(amp),
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
            n_done += 1
        print(f"  [OK] A={amp:.3f}  ({n_done}/{total})")

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Razões derivadas (sem interpretação)
# ---------------------------------------------------------------------------
def adicionar_razoes(df):
    df = df.copy()
    p0 = float(df.loc[df["amplitude"] == 0.0, "P_mean_k3"].median())
    df.attrs["P0_median_A0"] = p0

    A  = df["amplitude"].to_numpy()
    P3 = df["P_mean_k3"].to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        df["razao_simples_k3"] = np.where(A > 0, P3 / (A ** 2), np.nan)
        df["razao_sub_k3"]     = np.where(A > 0, (P3 - p0) / (A ** 2), np.nan)
    return df


# ---------------------------------------------------------------------------
# Gráficos (5)
# ---------------------------------------------------------------------------
def gerar_graficos(df, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    amplitudes = sorted(df["amplitude"].unique())

    # 1) Distribuição de P(k=3) por amplitude
    fig, ax = plt.subplots(figsize=(10, 5))
    data = [df.loc[df["amplitude"] == a, "P_mean_k3"].to_numpy() for a in amplitudes]
    ax.boxplot(data, showfliers=False)
    ax.set_xticks(range(1, len(amplitudes) + 1))
    ax.set_xticklabels([f"{a:.3f}" for a in amplitudes], rotation=45)
    ax.set_xlabel("Amplitude A")
    ax.set_ylabel("P(k=3)  [P_mean_k3]")
    ax.set_title("Distribuição de P(k=3) por amplitude (200 reps, boxplot sem outliers)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "01_distribuicao_Pk3.png", dpi=140)
    plt.close(fig)

    # 2) Mediana e média de P(k=3) vs A²
    med  = df.groupby("amplitude")["P_mean_k3"].median()
    mean = df.groupby("amplitude")["P_mean_k3"].mean()
    a_sq = np.array(amplitudes) ** 2
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(a_sq, med.values, "o-", label="mediana")
    ax.plot(a_sq, mean.values, "s--", label="média")
    ax.set_xlabel("A²")
    ax.set_ylabel("P(k=3)")
    ax.set_title("P(k=3) vs A² (mediana e média)")
    ax.legend(); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "02_Pk3_vs_A2.png", dpi=140)
    plt.close(fig)

    # 3) P(k=3)/A² e (P(k=3)-P0)/A² vs A
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, col, title in zip(
        axes,
        ["razao_simples_k3", "razao_sub_k3"],
        ["P(k=3)/A² vs A", "(P(k=3)-P0)/A² vs A"],
    ):
        med_r  = df.groupby("amplitude")[col].median()
        mean_r = df.groupby("amplitude")[col].mean()
        a_arr  = np.array(amplitudes)
        m = ~np.isnan(med_r.values)
        ax.plot(a_arr[m],  med_r.values[m],  "o-", label="mediana")
        ax.plot(a_arr[m],  mean_r.values[m], "s--", label="média")
        ax.set_xlabel("A"); ax.set_ylabel(col); ax.set_title(title)
        ax.legend(); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "03_razoes_vs_A.png", dpi=140)
    plt.close(fig)

    # 4) Espectro médio/mediano P(k) para k=0..12
    fig, ax = plt.subplots(figsize=(9, 5))
    ks = list(K_SPECTRUM)
    for a in amplitudes:
        means = [df.loc[df["amplitude"] == a, f"P_k{k}"].mean()  for k in ks]
        meds  = [df.loc[df["amplitude"] == a, f"P_k{k}"].median() for k in ks]
        ax.plot(ks, meds,  "o-",  label=f"A={a:.3f} (mediana)", alpha=0.9)
        ax.plot(ks, means, "x--", alpha=0.4)
    ax.set_yscale("log")
    ax.set_xlabel("k (bin FFT no eixo de injeção)")
    ax.set_ylabel("P(k)")
    ax.set_title("Espectro P(k) para k=0..12 (linha cheia=mediana; tracejada=média)")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(out_dir / "04_espectro_medio.png", dpi=140)
    plt.close(fig)

    # 5) P(k=6) vs A
    fig, ax = plt.subplots(figsize=(8, 5))
    med6  = df.groupby("amplitude")["P_k6"].median()
    mean6 = df.groupby("amplitude")["P_k6"].mean()
    ax.plot(amplitudes, med6.values,  "o-", label="mediana")
    ax.plot(amplitudes, mean6.values, "s--", label="média")
    ax.set_xlabel("A"); ax.set_ylabel("P(k=6)")
    ax.set_title("P(k=6) vs A  (k=6 = 2·k_target)")
    ax.legend(); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "05_Pk6_vs_A.png", dpi=140)
    plt.close(fig)

    print(f"[+] 5 gráficos salvos em: {out_dir}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = rodar_experimento()
    df = adicionar_razoes(df)

    csv_path = OUTPUT_DIR / "realizacoes.csv"
    df.to_csv(csv_path, index=False)
    print(f"[+] CSV por realização salvo em: {csv_path}")

    summary = (
        df.groupby("amplitude")
          .agg(
              R                 = ("rep", "count"),
              P_mean_k3_median  = ("P_mean_k3", "median"),
              P_mean_k3_mean    = ("P_mean_k3", "mean"),
              P_mean_k3_std     = ("P_mean_k3", "std"),
              P_pos_k3_median   = ("P_pos_k3", "median"),
              P_neg_k3_median   = ("P_neg_k3", "median"),
              P_k6_median       = ("P_k6", "median"),
              razao_simples_median = ("razao_simples_k3", "median"),
              razao_sub_median     = ("razao_sub_k3", "median"),
          )
          .reset_index()
    )
    summary.to_csv(OUTPUT_DIR / "resumo_por_amplitude.csv", index=False)
    print(f"[+] Resumo salvo em: {OUTPUT_DIR / 'resumo_por_amplitude.csv'}")
    print(f"[INFO] P0 (mediana de P_mean_k3 em A=0) = {df.attrs['P0_median_A0']:.6g}")

    # Sanidade (não é interpretação)
    print(f"[CHECK] conjugado:            {int(df['conjugado'].sum())}/{len(df)}")
    print(f"[CHECK] P_pos==P_neg rtol=1e-10: {bool(np.allclose(df['P_pos_k3'], df['P_neg_k3'], rtol=1e-10, atol=0))}")
    print(f"[CHECK] P_mean==P_pos  rtol=1e-10: {bool(np.allclose(df['P_mean_k3'], df['P_pos_k3'], rtol=1e-10, atol=0))}")
    print(f"[CHECK] N_realizado único:    {df['N_realizado'].unique().tolist()}")
    print(f"[CHECK] pos_idx, neg_idx:     {df['pos_idx'].unique().tolist()}, {df['neg_idx'].unique().tolist()}")

    gerar_graficos(df, OUTPUT_DIR)
    print("[DONE]")