#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Projeto Tempo, Ondas e Observador
Teste Gepeto: recuperação de uma onda espacial conhecida em catálogo 3D sintético.

Objetivo:
  1) Gerar pontos 3D com uma distribuição de fundo + uma modulação sinusoidal
     de comprimento de onda conhecido (ex.: 100 Mpc).
  2) Medir se a frequência espacial injetada é recuperada pelo espectro de potência.
  3) Comparar com catálogos sem onda, usando exatamente o mesmo volume e N.
  4) Repetir simulações para estimar taxa de recuperação e falsos positivos.

Importante:
  - Este é um teste de calibração sintético, NÃO uma análise cosmológica.
  - O volume é uma caixa periódica idealizada, não a máscara real do SDSS.
  - O resultado não prova a existência da "Grande Onda"; testa o instrumento.
  - Usa somente NumPy, SciPy e Matplotlib.

Instalação:
  pip install numpy scipy matplotlib

Execução:
  python teste_recuperacao_onda_3d_gepeto.py
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist


@dataclass
class Config:
    n_galaxies: int = 12000
    box_mpc: float = 300.0
    wavelength_mpc: float = 100.0
    amplitude: float = 0.20
    grid_n: int = 64
    repetitions: int = 40
    seed: int = 42


def generate_catalog(
    n: int,
    box: float,
    wavelength: float,
    amplitude: float,
    rng: np.random.Generator,
    inject_wave: bool,
) -> np.ndarray:
    """
    Rejeição amostral em caixa periódica.
    Densidade-alvo proporcional a 1 + A*cos(2*pi*x/lambda).
    amplitude deve estar entre 0 e <1.
    """
    if not (0.0 <= amplitude < 1.0):
        raise ValueError("A amplitude deve estar no intervalo [0, 1).")
    if wavelength <= 0 or box <= 0 or n <= 0:
        raise ValueError("N, caixa e comprimento de onda devem ser positivos.")

    pts = np.empty((n, 3), dtype=float)
    filled = 0
    max_density = 1.0 + amplitude if inject_wave else 1.0

    while filled < n:
        batch_n = max(2000, 2 * (n - filled))
        candidate = rng.uniform(0.0, box, size=(batch_n, 3))
        if inject_wave:
            density = 1.0 + amplitude * np.cos(
                2.0 * np.pi * candidate[:, 0] / wavelength
            )
            keep = rng.random(batch_n) < density / max_density
        else:
            keep = np.ones(batch_n, dtype=bool)

        accepted = candidate[keep]
        take = min(len(accepted), n - filled)
        if take:
            pts[filled:filled + take] = accepted[:take]
            filled += take

    return pts


def density_grid(points: np.ndarray, box: float, ngrid: int) -> np.ndarray:
    """Histograma 3D; retorna densidade contrastada delta = rho/<rho> - 1."""
    hist, _ = np.histogramdd(
        points,
        bins=(ngrid, ngrid, ngrid),
        range=((0, box), (0, box), (0, box)),
    )
    mean = hist.mean()
    if mean <= 0:
        raise ValueError("Grade vazia.")
    return hist / mean - 1.0


def power_spectrum_1d(delta: np.ndarray, box: float):
    """
    Espectro isotrópico simplificado.
    Frequências são convertidas para k angular (rad/Mpc): k=2*pi/lambda.
    """
    n = delta.shape[0]
    if delta.shape != (n, n, n):
        raise ValueError("A grade precisa ser cúbica 3D.")

    # Janela Hann separável para reduzir vazamento espectral nas bordas.
    # O sinal de teste é periódico se box/lambda for inteiro, mas a janela
    # torna o procedimento mais conservador e igual para todos os casos.
    win1 = np.hanning(n)
    window = win1[:, None, None] * win1[None, :, None] * win1[None, None, :]
    field = (delta - delta.mean()) * window

    ft = np.fft.fftn(field)
    power = np.abs(ft) ** 2

    dx = box / n
    f = np.fft.fftfreq(n, d=dx)
    k_axis = 2.0 * np.pi * f
    kx, ky, kz = np.meshgrid(k_axis, k_axis, k_axis, indexing="ij")
    kmag = np.sqrt(kx*kx + ky*ky + kz*kz)

    k_fund = 2.0 * np.pi / box
    k_nyquist = np.pi / dx
    bins = np.linspace(k_fund * 0.5, k_nyquist, 24)
    which = np.digitize(kmag.ravel(), bins) - 1

    k_centers = 0.5 * (bins[:-1] + bins[1:])
    p_avg = np.full(len(k_centers), np.nan)
    p_count = np.zeros(len(k_centers), dtype=int)
    flat_p = power.ravel()
    flat_k = kmag.ravel()

    for i in range(len(k_centers)):
        mask = (which == i) & (flat_k > 0)
        if np.any(mask):
            p_avg[i] = np.mean(flat_p[mask])
            p_count[i] = int(mask.sum())

    return k_centers, p_avg, p_count


def interpolate_power(k: np.ndarray, p: np.ndarray, target_k: float) -> float:
    valid = np.isfinite(p) & (p > 0)
    if valid.sum() < 2:
        return float("nan")
    # Interpolação em log(k)-log(P) para comparação relativa.
    kval = k[valid]
    pval = p[valid]
    order = np.argsort(kval)
    kval, pval = kval[order], pval[order]
    if target_k < kval.min() or target_k > kval.max():
        return float("nan")
    return float(np.exp(np.interp(np.log(target_k), np.log(kval), np.log(pval))))


def run(cfg: Config):
    rng = np.random.default_rng(cfg.seed)
    target_k = 2.0 * np.pi / cfg.wavelength_mpc

    print("=" * 72)
    print("TESTE DE RECUPERAÇÃO DE ONDA 3D — GEPETO")
    print("=" * 72)
    print(f"Galáxias por catálogo : {cfg.n_galaxies:,}")
    print(f"Caixa                 : {cfg.box_mpc:.1f} Mpc por lado")
    print(f"Comprimento injetado  : {cfg.wavelength_mpc:.1f} Mpc")
    print(f"k esperado            : {target_k:.5f} rad/Mpc")
    print(f"Amplitude de modulação: {cfg.amplitude:.2f}")
    print(f"Grade                 : {cfg.grid_n}^3")
    print(f"Repetições por classe : {cfg.repetitions}")
    print("")

    spectra = {"Sem onda": [], "Com onda": []}
    target_powers = {"Sem onda": [], "Com onda": []}
    peak_ks = {"Sem onda": [], "Com onda": []}

    for label, inject in (("Sem onda", False), ("Com onda", True)):
        for rep in range(cfg.repetitions):
            # Sementes diferentes por repetição, mas o N e o volume são iguais.
            pts = generate_catalog(
                cfg.n_galaxies,
                cfg.box_mpc,
                cfg.wavelength_mpc,
                cfg.amplitude,
                rng,
                inject_wave=inject,
            )
            delta = density_grid(pts, cfg.box_mpc, cfg.grid_n)
            k, p, counts = power_spectrum_1d(delta, cfg.box_mpc)

            # Faixa local ao redor do k esperado; evita selecionar um pico
            # arbitrário muito distante da escala testada.
            local = (
                np.isfinite(p)
                & (k >= target_k * 0.70)
                & (k <= target_k * 1.30)
                & (counts > 0)
            )
            peak_k = float(k[local][np.nanargmax(p[local])]) if np.any(local) else np.nan
            target_power = interpolate_power(k, p, target_k)

            spectra[label].append((k, p))
            target_powers[label].append(target_power)
            peak_ks[label].append(peak_k)

        print(f"Concluído: {label} ({cfg.repetitions}/{cfg.repetitions})")

    null_p = np.asarray(target_powers["Sem onda"], dtype=float)
    signal_p = np.asarray(target_powers["Com onda"], dtype=float)
    null_peaks = np.asarray(peak_ks["Sem onda"], dtype=float)
    signal_peaks = np.asarray(peak_ks["Com onda"], dtype=float)

    null_med = np.nanmedian(null_p)
    signal_med = np.nanmedian(signal_p)
    ratio = signal_med / null_med if null_med > 0 else np.nan

    # Critério de detecção exploratório: potência no k-alvo acima do percentil
    # 95 dos controles sem onda. Deve ser tratado como calibração, não p-valor
    # cosmológico; para análise formal seria necessário controlar múltiplas buscas.
    threshold = np.nanpercentile(null_p, 95)
    detections = signal_p > threshold
    recovery = np.nanmean(detections)

    print("\n--- RESUMO ---")
    print(f"Mediana potência no k-alvo, sem onda : {null_med:.6g}")
    print(f"Mediana potência no k-alvo, com onda : {signal_med:.6g}")
    print(f"Razão mediana com/sem onda            : {ratio:.3f}")
    print(f"Limite exploratório (P95 sem onda)    : {threshold:.6g}")
    print(f"Recuperação da onda injetada           : {recovery:.1%}")
    print(
        "Interpretação: se a recuperação for baixa, o pipeline precisa de "
        "calibração antes de interpretar uma não-detecção em dados reais."
    )

    # Gráfico 1: espectros médios e dispersão entre catálogos.
    fig, ax = plt.subplots(figsize=(10, 6))
    for label in ("Sem onda", "Com onda"):
        all_k = spectra[label][0][0]
        pmat = np.array([item[1] for item in spectra[label]])
        med = np.nanmedian(pmat, axis=0)
        lo = np.nanpercentile(pmat, 16, axis=0)
        hi = np.nanpercentile(pmat, 84, axis=0)
        valid = np.isfinite(med) & (med > 0)
        ax.plot(all_k[valid], med[valid], label=label)
        ax.fill_between(all_k[valid], lo[valid], hi[valid], alpha=0.2)

    ax.axvline(target_k, linestyle="--", label=f"k injetado = {target_k:.4f}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("k angular (rad/Mpc)")
    ax.set_ylabel("Potência FFT (unidades arbitrárias)")
    ax.set_title("Teste sintético: recuperação de uma modulação espacial 3D")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig("teste_recuperacao_onda_espectro.png", dpi=160)
    plt.close(fig)

    # Gráfico 2: distribuição da potência no k-alvo por classe.
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(
        [null_p[np.isfinite(null_p)], signal_p[np.isfinite(signal_p)]],
        tick_labels=["Sem onda", "Com onda"],
    )
    ax.axhline(threshold, linestyle="--", label="P95 dos controles sem onda")
    ax.set_ylabel("Potência no k-alvo (unidades arbitrárias)")
    ax.set_title("Separação entre controles e sinais injetados")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig("teste_recuperacao_onda_distribuicao.png", dpi=160)
    plt.close(fig)

    print("\nGráficos salvos:")
    print("  - teste_recuperacao_onda_espectro.png")
    print("  - teste_recuperacao_onda_distribuicao.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=12000, help="Galáxias por catálogo")
    parser.add_argument("--box", type=float, default=300.0, help="Lado da caixa em Mpc")
    parser.add_argument("--wavelength", type=float, default=100.0, help="Onda em Mpc")
    parser.add_argument("--amplitude", type=float, default=0.20, help="Amplitude da modulação (0 a <1)")
    parser.add_argument("--grid", type=int, default=64, help="Número de bins por eixo")
    parser.add_argument("--reps", type=int, default=40, help="Repetições por classe")
    parser.add_argument("--seed", type=int, default=42, help="Semente aleatória")
    args = parser.parse_args()

    cfg = Config(
        n_galaxies=args.n,
        box_mpc=args.box,
        wavelength_mpc=args.wavelength,
        amplitude=args.amplitude,
        grid_n=args.grid,
        repetitions=args.reps,
        seed=args.seed,
    )
    run(cfg)


if __name__ == "__main__":
    main()
