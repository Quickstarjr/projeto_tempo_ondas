#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoria do estimador de potência — Projeto Tempo, Ondas e Observador.
Reproduz as funções originais e adiciona diagnóstico (P_pos, P_neg, índices, etc.).
NÃO altera o script original.
"""

import numpy as np
import pandas as pd
from pathlib import Path


# ---------------------------------------------------------------------------
# Funções originais (cópia fiel do original)
# ---------------------------------------------------------------------------

def gerar_catalogo_modulado(n, box, wavelength, amplitude, rng, axis=0):
    """Amostragem por rejeição em caixa periódica.
    Densidade ∝ 1 + A*cos(2π*x_axis/wavelength)."""
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
# Versão detalhada do estimador
# ---------------------------------------------------------------------------

def potencia_no_k_alvo_detalhado(points, box, grid_n, wavelength, axis=0):
    """
    Retorna dicionário com:
      P_pos, P_neg, P_mean, P_max,
      pos_idx, neg_idx, conjugado (bool), N_realizado.
    """
    hist, _ = np.histogramdd(
        points,
        bins=(grid_n, grid_n, grid_n),
        range=((0, box), (0, box), (0, box)),
    )
    field = hist.astype(np.float64) - hist.mean()

    # Janela Hann 3D (idêntica ao original)
    win1 = np.hanning(grid_n)
    window = win1[:, None, None] * win1[None, :, None] * win1[None, None, :]
    field *= window

    ft = np.fft.fftn(field)
    power = np.abs(ft) ** 2

    freq = np.fft.fftfreq(grid_n, d=box / grid_n) * 2 * np.pi
    k_target = 2 * np.pi / wavelength

    idx_pos = int(np.argmin(np.abs(freq - k_target)))
    idx_neg = int(np.argmin(np.abs(freq + k_target)))

    if axis == 0:
        p_pos = power[idx_pos, 0, 0]
        p_neg = power[idx_neg, 0, 0]
    elif axis == 1:
        p_pos = power[0, idx_pos, 0]
        p_neg = power[0, idx_neg, 0]
    else:
        p_pos = power[0, 0, idx_pos]
        p_neg = power[0, 0, idx_neg]

    p_mean = 0.5 * (p_pos + p_neg)
    p_max = max(p_pos, p_neg)

    # Teste de conjugação: idx_pos + idx_neg ≡ 0 (mod N)
    conjugado = ((idx_pos + idx_neg) % grid_n == 0)

    return {
        "P_pos": float(p_pos),
        "P_neg": float(p_neg),
        "P_mean": float(p_mean),
        "P_max": float(p_max),
        "pos_idx": idx_pos,
        "neg_idx": idx_neg,
        "conjugado": bool(conjugado),
        "N_realizado": len(points),
    }


# ---------------------------------------------------------------------------
# Execução controlada (mesma lógica de seeds do original)
# ---------------------------------------------------------------------------

def rodar_experimento(
    N=12000,
    BOX=300.0,
    WAVELENGTH=100.0,
    GRID=64,
    REPS=30,
    amplitudes=(0.0, 0.01, 0.05, 0.10, 0.20),
    seed_master=20261021,
    axis=0,
    output_dir="outputs/auditoria",
):
    """
    Executa o experimento com a mesma lógica de seeds do original.
    Retorna DataFrame com uma linha por realização.
    """
    rng_master = np.random.default_rng(seed_master)
    linhas = []

    for amp in amplitudes:
        for rep in range(REPS):
            seed = int(rng_master.integers(0, 2**32 - 1))
            rng = np.random.default_rng(seed)
            pts = gerar_catalogo_modulado(N, BOX, WAVELENGTH, amp, rng, axis=axis)
            diag = potencia_no_k_alvo_detalhado(
                pts, BOX, GRID, WAVELENGTH, axis=axis
            )
            linhas.append({
                "seed": seed,
                "rep": rep,
                "amplitude": amp,
                "axis": axis,
                "N_realizado": diag["N_realizado"],
                "P_pos": diag["P_pos"],
                "P_neg": diag["P_neg"],
                "P_mean": diag["P_mean"],
                "P_max": diag["P_max"],
                "pos_idx": diag["pos_idx"],
                "neg_idx": diag["neg_idx"],
                "conjugado": diag["conjugado"],
            })

    df = pd.DataFrame(linhas)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "auditoria_realizacoes.csv"
    df.to_csv(csv_path, index=False)
    print(f"[+] CSV salvo em: {csv_path}")
    return df


if __name__ == "__main__":
    df = rodar_experimento()
    # Resumo rápido
    print("\nResumo por amplitude:")
    print(df.groupby("amplitude")[["P_pos", "P_neg", "P_mean", "P_max"]].median())
    print("\nTeste de conjugação (todas as linhas):")
    print("conjugado == True:", df["conjugado"].all())
    print("P_pos == P_neg (rtol=1e-10):",
          np.allclose(df["P_pos"], df["P_neg"], rtol=1e-10))
    print("N_realizado único:", df["N_realizado"].unique())