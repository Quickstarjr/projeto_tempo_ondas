#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificação do Cálculo de Potência — Missão do Gepeto
Projeto Tempo, Ondas e Observador

Objetivo:
  Verificar se o cálculo da potência no k-alvo está consistente:
  1. A potência deve crescer proporcionalmente ao QUADRADO da amplitude
     (P ∝ A²) em uma transformada de Fourier.
  2. Na ausência de onda (A=0), a potência deve ser estável (apenas ruído).
  3. A orientação da onda não deve afetar a detecção.

Este script responde à pergunta:
  "O cálculo da potência está medindo o sinal pretendido,
   ou algum artefato da grade/processamento?"
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def gerar_catalogo_modulado(n, box, wavelength, amplitude, rng, axis=0):
    """
    Amostragem por rejeição em caixa periódica.
    Densidade ∝ 1 + A*cos(2π*x_axis/wavelength)
    """
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


def potencia_no_k_alvo(points, box, grid_n, wavelength, axis=0):
    """
    Mede a potência no modo FFT mais próximo do k-alvo.
    Usa janela de Hann 3D para reduzir vazamento espectral.
    """
    hist, _ = np.histogramdd(
        points,
        bins=(grid_n, grid_n, grid_n),
        range=((0, box), (0, box), (0, box)),
    )
    field = hist.astype(np.float64) - hist.mean()

    # Janela Hann 3D
    win1 = np.hanning(grid_n)
    window = win1[:, None, None] * win1[None, :, None] * win1[None, None, :]
    field *= window

    ft = np.fft.fftn(field)
    power = np.abs(ft) ** 2

    freq = np.fft.fftfreq(grid_n, d=box / grid_n) * 2 * np.pi
    k_target = 2 * np.pi / wavelength

    # Encontrar o índice mais próximo de k_target no eixo da onda
    idx_pos = int(np.argmin(np.abs(freq - k_target)))
    idx_neg = int(np.argmin(np.abs(freq + k_target)))

    # Buscar o modo (k_target, 0, 0) e (-k_target, 0, 0) conforme o eixo
    if axis == 0:
        p_pos = power[idx_pos, 0, 0]
        p_neg = power[idx_neg, 0, 0]
    elif axis == 1:
        p_pos = power[0, idx_pos, 0]
        p_neg = power[0, idx_neg, 0]
    else:
        p_pos = power[0, 0, idx_pos]
        p_neg = power[0, 0, idx_neg]

    return float(max(p_pos, p_neg))


def main():
    print("=" * 70)
    print("VERIFICAÇÃO DO CÁLCULO DE POTÊNCIA — MISSÃO DO GEPETO")
    print("=" * 70)

    # Parâmetros
    N = 12000
    BOX = 300.0
    WAVELENGTH = 100.0
    GRID = 64
    REPS = 30  # Repetições por amplitude

    # Amplitudes a testar (incluindo 0 para o controle)
    amplitudes = [0.0, 0.01, 0.05, 0.10, 0.20]

    # Teste 1: Potência vs Amplitude (mesmo eixo)
    print("\n[TESTE 1] Potência vs Amplitude (eixo X)...")
    print(f"  N={N}, Box={BOX} Mpc, λ={WAVELENGTH} Mpc, Grid={GRID}³, Reps={REPS}")

    results_amp = {a: [] for a in amplitudes}
    rng_master = np.random.default_rng(20261021)

    for amp in amplitudes:
        for rep in range(REPS):
            rng = np.random.default_rng(rng_master.integers(0, 2**32 - 1))
            pts = gerar_catalogo_modulado(N, BOX, WAVELENGTH, amp, rng, axis=0)
            p = potencia_no_k_alvo(pts, BOX, GRID, WAVELENGTH, axis=0)
            results_amp[amp].append(p)
        mediana = np.median(results_amp[amp])
        print(f"  A={amp:.2f} → Mediana P(k) = {mediana:.4e}")

    # Teste 2: Orientação da onda
    print("\n[TESTE 2] Independência da Orientação (A=0.10)...")
    results_axis = {axis: [] for axis in [0, 1, 2]}
    amp_test = 0.10

    for axis in [0, 1, 2]:
        for rep in range(REPS):
            rng = np.random.default_rng(rng_master.integers(0, 2**32 - 1))
            pts = gerar_catalogo_modulado(N, BOX, WAVELENGTH, amp_test, rng, axis=axis)
            p = potencia_no_k_alvo(pts, BOX, GRID, WAVELENGTH, axis=axis)
            results_axis[axis].append(p)
        mediana = np.median(results_axis[axis])
        print(f"  Eixo {['X', 'Y', 'Z'][axis]} → Mediana P(k) = {mediana:.4e}")

    # --- Análise de consistência ---
    print("\n" + "=" * 70)
    print("ANÁLISE DE CONSISTÊNCIA")
    print("=" * 70)

    # Teste 1a: Potência deve crescer como A²
    med_0 = np.median(results_amp[0.0])
    print(f"\n[1a] Relação P ∝ A²:")
    print(f"     P(A=0) = {med_0:.4e} (baseline de ruído)")
    print(f"     {'A':>6} | {'A²':>10} | {'P(k)':>12} | {'P(k) - P(0)':>14} | {'(P-P0)/A²':>12}")
    for amp in amplitudes:
        if amp == 0:
            continue
        p_med = np.median(results_amp[amp])
        delta_p = p_med - med_0
        ratio = delta_p / (amp**2) if amp > 0 else 0
        print(f"     {amp:>6.2f} | {amp**2:>10.4f} | {p_med:>12.4e} | {delta_p:>14.4e} | {ratio:>12.4e}")

    # Teste 1b: A razão (P-P0)/A² deve ser aproximadamente constante
    razoes = []
    for amp in amplitudes:
        if amp == 0:
            continue
        p_med = np.median(results_amp[amp])
        delta_p = p_med - med_0
        if delta_p > 0:
            razoes.append(delta_p / (amp**2))

    if len(razoes) >= 2:
        razao_media = np.mean(razoes)
        razao_std = np.std(razoes)
        cv = razao_std / razao_media if razao_media > 0 else float('inf')
        print(f"\n[1b] Razão média (P-P0)/A²: {razao_media:.4e} ± {razao_std:.4e}")
        print(f"     Coeficiente de variação: {cv:.3f}")
        if cv < 0.5:
            print("     → CONSISTENTE com P ∝ A² (CV < 0.5)")
        else:
            print("     → ATENÇÃO: CV alto, possível não-linearidade ou artefato.")

    # Teste 2: Independência da orientação
    med_x = np.median(results_axis[0])
    med_y = np.median(results_axis[1])
    med_z = np.median(results_axis[2])
    print(f"\n[2] Independência da orientação (A=0.10):")
    print(f"     X: {med_x:.4e}")
    print(f"     Y: {med_y:.4e}")
    print(f"     Z: {med_z:.4e}")
    max_dev = max(abs(med_x - med_y), abs(med_y - med_z), abs(med_x - med_z)) / np.mean([med_x, med_y, med_z])
    print(f"     Desvio máximo relativo entre eixos: {max_dev:.3f}")
    if max_dev < 0.2:
        print("     → CONSISTENTE entre orientações (desvio < 20%)")
    else:
        print("     → ATENÇÃO: detecção depende da orientação.")

    # --- Gráficos ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Painel 1: P vs A (com linha de A²)
    ax1 = axes[0]
    meds = [np.median(results_amp[a]) for a in amplitudes]
    ax1.plot(amplitudes, meds, 'o-', label='Mediana P(k)', color='blue')
    ax1.axhline(med_0, color='gray', linestyle='--', label='P(A=0) = ruído')
    # Linha teórica de A² ajustada
    amp_arr = np.array([a for a in amplitudes if a > 0])
    if len(razoes) > 0:
        p_theory = med_0 + razao_media * amp_arr**2
        ax1.plot(amp_arr, p_theory, 'r--', label=f'P ∝ A² (ajuste)', alpha=0.7)
    ax1.set_xlabel('Amplitude injetada')
    ax1.set_ylabel('Potência no k-alvo')
    ax1.set_title('Teste 1: P(k) vs Amplitude (deve seguir A²)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Painel 2: Distribuições por amplitude
    ax2 = axes[1]
    box_data = [results_amp[a] for a in amplitudes]
    labels = [f'A={a:.2f}' for a in amplitudes]
    ax2.boxplot(box_data, tick_labels=labels, showfliers=False)
    ax2.set_ylabel('Potência no k-alvo')
    ax2.set_title('Teste 1: Distribuições de P(k) por amplitude')
    ax2.grid(True, alpha=0.3)
    plt.setp(ax2.get_xticklabels(), rotation=45)

    plt.tight_layout()
    pasta = Path('outputs/reports/verificacao_potencia_gepeto')
    pasta.mkdir(parents=True, exist_ok=True)
    fig.savefig(pasta / 'verificacao_potencia.png', dpi=140)
    plt.close()
    print(f"\n[+] Gráfico salvo em: {pasta}/verificacao_potencia.png")

    # --- Salvar CSV ---
    import csv
    with open(pasta / 'verificacao_potencia.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['amplitude', 'mediana_P(k)', 'desvio_P(k)', 'delta_vs_zero'])
        for amp in amplitudes:
            vals = np.array(results_amp[amp])
            writer.writerow([
                amp,
                np.median(vals),
                np.std(vals),
                np.median(vals) - med_0,
            ])
    print(f"[+] CSV salvo em: {pasta}/verificacao_potencia.csv")


if __name__ == "__main__":
    main()