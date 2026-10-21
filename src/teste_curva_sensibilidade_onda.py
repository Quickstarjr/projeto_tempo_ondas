#!/usr/bin/env python3
"""
Curva de sensibilidade para recuperação de uma modulação espacial 3D.

Este teste sintético:
- gera catálogos uniformes e catálogos com uma modulação sinusoidal conhecida;
- mede a potência Fourier no modo-alvo (lambda especificado);
- calibra o limiar com o percentil dos catálogos sem onda;
- estima taxa de detecção e falsos positivos;
- grava CSVs e um gráfico.

IMPORTANTE:
É um teste de validação de método em uma caixa periódica idealizada.
Não é um modelo completo de BAO nem uma simulação realista do SDSS.
"""

import argparse
import csv
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def sample_catalog(n, box, amplitude, wavelength, rng, axis=0, phase=None):
    """Amostra pontos uniformes com probabilidade modulada por 1 + A*cos(k*x+fase)."""
    if phase is None:
        phase = rng.uniform(0, 2 * np.pi)

    # Rejeição: a densidade é proporcional a 1 + A*cos(k*x + fase).
    # A precisa ficar abaixo de 1 para a densidade nunca ser negativa.
    if not (0 <= amplitude < 1):
        raise ValueError("A amplitude precisa estar no intervalo [0, 1).")

    pts = np.empty((n, 3), dtype=float)
    filled = 0
    k = 2 * np.pi / wavelength
    while filled < n:
        batch = max(2048, 2 * (n - filled))
        candidate = rng.uniform(0.0, box, size=(batch, 3))
        if amplitude == 0:
            accepted = np.ones(batch, dtype=bool)
        else:
            prob = (1.0 + amplitude * np.cos(k * candidate[:, axis] + phase)) / (1.0 + amplitude)
            accepted = rng.random(batch) < prob
        take = candidate[accepted]
        count = min(len(take), n - filled)
        if count:
            pts[filled:filled + count] = take[:count]
            filled += count
    return pts


def power_at_target(points, box, grid_n, wavelength):
    """Deposita pontos numa grade e mede potência no modo FFT mais próximo de k-alvo."""
    # Histograma 3D; a grade representa densidade de contagem por célula.
    hist, _ = np.histogramdd(
        points,
        bins=(grid_n, grid_n, grid_n),
        range=((0, box), (0, box), (0, box)),
    )
    field = hist.astype(np.float64)
    field -= field.mean()

    # Janela de Hann 3D reduz vazamento espectral nas bordas.
    # Como a onda-alvo é escolhida para caber na caixa, a janela pode alargar o modo;
    # usamos o máximo numa pequena vizinhança do modo-alvo.
    win1 = np.hanning(grid_n)
    window = win1[:, None, None] * win1[None, :, None] * win1[None, None, :]
    field *= window

    ft = np.fft.fftn(field)
    power = np.abs(ft) ** 2

    freq = np.fft.fftfreq(grid_n, d=box / grid_n) * 2 * np.pi
    kx, ky, kz = np.meshgrid(freq, freq, freq, indexing="ij")
    kmag = np.sqrt(kx * kx + ky * ky + kz * kz)
    k_target = 2 * np.pi / wavelength

    # A onda é injetada ao longo do eixo x: buscar modos ±kx, ky≈0, kz≈0.
    # Permitir o bin mais próximo, com tolerância de meio bin.
    idx = int(np.argmin(np.abs(freq - k_target)))
    idx_neg = int(np.argmin(np.abs(freq + k_target)))
    candidates = [power[idx, 0, 0], power[idx_neg, 0, 0]]
    return float(max(candidates)), float(k_target), float(abs(freq[idx] - k_target))


def run(args):
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    master_rng = np.random.default_rng(args.seed)

    # Para que a onda encaixe exatamente na caixa periódica, lambda deve dividir L.
    cycles = args.box / args.wavelength
    if abs(cycles - round(cycles)) > 1e-8:
        print("AVISO: comprimento de onda não cabe um número inteiro de ciclos na caixa; "
              "pode haver vazamento espectral. Idealmente escolha box/wavelength inteiro.")

    amplitudes = [float(x) for x in args.amplitudes.split(",")]
    if any(a < 0 or a >= 1 for a in amplitudes):
        raise ValueError("Todas as amplitudes devem estar entre 0 e 1.")

    null_powers = []
    for rep in range(args.reps):
        rng = np.random.default_rng(master_rng.integers(0, 2**32 - 1))
        pts = sample_catalog(args.n, args.box, 0.0, args.wavelength, rng, axis=args.axis)
        p, _, _ = power_at_target(pts, args.box, args.grid, args.wavelength)
        null_powers.append(p)
        if (rep + 1) % max(1, args.reps // 5) == 0:
            print(f"Controles sem onda: {rep+1}/{args.reps}")

    # Limiar pré-definido a partir dos controles nulos.
    threshold = float(np.quantile(null_powers, args.quantile))
    null_false_positive = float(np.mean(np.asarray(null_powers) > threshold))

    rows = []
    all_signal_powers = []
    print("\n--- Curva de sensibilidade ---")
    print(f"Limiar P{args.quantile*100:.1f} dos controles sem onda: {threshold:.6g}")
    print(f"Falsos positivos observados nos controles usados para calibrar: {null_false_positive:.3f}")
    print("Amplitude | Detecção | Potência mediana | Razão mediana")

    for amp in amplitudes:
        powers = []
        for rep in range(args.reps):
            rng = np.random.default_rng(master_rng.integers(0, 2**32 - 1))
            phase = rng.uniform(0, 2 * np.pi)
            pts = sample_catalog(args.n, args.box, amp, args.wavelength, rng,
                                 axis=args.axis, phase=phase)
            p, _, _ = power_at_target(pts, args.box, args.grid, args.wavelength)
            powers.append(p)
        powers_arr = np.asarray(powers)
        detection = float(np.mean(powers_arr > threshold))
        med = float(np.median(powers_arr))
        null_med = float(np.median(null_powers))
        ratio = med / null_med if null_med > 0 else float("nan")
        all_signal_powers.append(powers_arr)

        rows.append({
            "amplitude_injetada": amp,
            "n_galaxias": args.n,
            "repeticoes": args.reps,
            "box_mpc": args.box,
            "comprimento_onda_mpc": args.wavelength,
            "k_alvo_rad_mpc": 2 * np.pi / args.wavelength,
            "grade": args.grid,
            "quantil_limiar": args.quantile,
            "limiar_potencia": threshold,
            "taxa_deteccao": detection,
            "potencia_mediana_com_onda": med,
            "potencia_mediana_sem_onda": null_med,
            "razao_mediana": ratio,
            "falsos_positivos_controles_calibracao": null_false_positive,
            "nota": "caixa idealizada; nao e modelo completo de BAO/SDSS",
        })
        print(f"{amp:8.3f} | {detection:7.1%} | {med:15.6g} | {ratio:13.3f}")

    csv_path = outdir / "curva_sensibilidade_onda.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    null_csv = outdir / "controles_sem_onda.csv"
    with null_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["repeticao", "potencia_k_alvo"])
        writer.writerows(enumerate(null_powers, start=1))

    # Plot 1: curva de detecção
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot([r["amplitude_injetada"] * 100 for r in rows],
            [r["taxa_deteccao"] * 100 for r in rows], marker="o")
    ax.axhline(args.quantile * 100, linestyle="--",
               label=f"Referência nominal P{args.quantile*100:.0f}")
    ax.set_xlabel("Amplitude de modulação injetada (%)")
    ax.set_ylabel("Catálogos acima do limiar (%)")
    ax.set_ylim(-2, 102)
    ax.set_title("Curva de sensibilidade — onda 3D sintética")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    plot_path = outdir / "curva_sensibilidade_onda.png"
    fig.savefig(plot_path, dpi=160)
    plt.close(fig)

    # Plot 2: distribuições de potência por amplitude
    fig, ax = plt.subplots(figsize=(9, 5))
    plot_data = [np.asarray(null_powers)] + all_signal_powers
    labels = ["Sem onda"] + [f"{a*100:.0f}%" for a in amplitudes]
    ax.boxplot(plot_data, tick_labels=labels, showfliers=False)
    ax.axhline(threshold, linestyle="--", label=f"Limiar P{args.quantile*100:.0f}")
    ax.set_xlabel("Amplitude injetada")
    ax.set_ylabel("Potência no modo-alvo")
    ax.set_title("Distribuições da estatística de detecção")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    dist_path = outdir / "distribuicoes_potencia_onda.png"
    fig.savefig(dist_path, dpi=160)
    plt.close(fig)

    print("\nArquivos salvos:")
    print(f"  - {csv_path}")
    print(f"  - {null_csv}")
    print(f"  - {plot_path}")
    print(f"  - {dist_path}")
    print("\nNota: a taxa de detecção depende do limiar e deste modelo sintético. "
          "Para uma taxa de falso positivo independente, use controles nulos separados "
          "dos usados para calibrar o limiar.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=12000, help="pontos por catálogo (padrão: 12000)")
    parser.add_argument("--box", type=float, default=300.0, help="lado da caixa em Mpc")
    parser.add_argument("--wavelength", type=float, default=100.0, help="comprimento de onda em Mpc")
    parser.add_argument("--grid", type=int, default=64, help="resolução da grade 3D")
    parser.add_argument("--reps", type=int, default=100, help="repetições por cenário")
    parser.add_argument("--amplitudes", default="0.01,0.02,0.03,0.05,0.075,0.10,0.15,0.20",
                        help="lista de amplitudes separadas por vírgula")
    parser.add_argument("--quantile", type=float, default=0.95, help="quantil para o limiar nulo (padrão: 0.95)")
    parser.add_argument("--axis", type=int, choices=[0, 1, 2], default=0, help="eixo da onda")
    parser.add_argument("--seed", type=int, default=20261021, help="semente aleatória")
    parser.add_argument("--outdir", default="outputs/reports/curva_sensibilidade_onda",
                        help="pasta de saída")
    args = parser.parse_args()
    if args.n < 1 or args.grid < 8 or args.reps < 2:
        parser.error("--n deve ser >=1, --grid >=8 e --reps >=2")
    if not 0 < args.quantile < 1:
        parser.error("--quantile precisa estar entre 0 e 1")
    run(args)


if __name__ == "__main__":
    main()
