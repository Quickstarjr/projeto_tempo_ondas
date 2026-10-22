#!/usr/bin/env python3
"""Avalia a sensibilidade da seleção de galáxias à posição da caixa."""

import numpy as np
import pandas as pd


def main():
    caminho = "outputs/reports/galaxias_tamanho/dados.csv"
    df = pd.read_csv(caminho)

    x = df["x_mpc"].to_numpy(dtype=float)
    y = df["y_mpc"].to_numpy(dtype=float)
    z = (
        df["z_mpc"].to_numpy(dtype=float)
        if "z_mpc" in df.columns
        else df["dist_mpc"].to_numpy(dtype=float)
        * np.sin(np.radians(df["dec"].to_numpy(dtype=float)))
    )

    pontos = np.column_stack([x, y, z])
    pontos = pontos[np.isfinite(pontos).all(axis=1)]

    minimo = pontos.min(axis=0)
    maximo = pontos.max(axis=0)
    amplitudes = maximo - minimo

    # Reproduz a regra de L_real do script original.
    L = float(amplitudes.max())
    centro = (minimo + maximo) / 2

    # Cada caixa tem o mesmo lado. Só mudamos seu centro.
    deslocamentos = [
        ("centro dos limites", [0, 0, 0]),
        ("X + 1/4 L", [L/4, 0, 0]),
        ("X - 1/4 L", [-L/4, 0, 0]),
        ("Y + 1/4 L", [0, L/4, 0]),
        ("Y - 1/4 L", [0, -L/4, 0]),
        ("Z + 1/4 L", [0, 0, L/4]),
        ("Z - 1/4 L", [0, 0, -L/4]),
        ("XYZ + 1/4 L", [L/4, L/4, L/4]),
    ]

    print("=" * 76)
    print("AUDITORIA DA POSIÇÃO DA CAIXA — GEPETO")
    print("=" * 76)
    print(f"Galáxias válidas: {len(pontos)}")
    print(f"Lado da caixa L : {L:.6f} Mpc")
    print(f"Centro dos limites: ({centro[0]:.3f}, "
          f"{centro[1]:.3f}, {centro[2]:.3f}) Mpc")
    print(f"Extensões X/Y/Z: {amplitudes[0]:.3f} / "
          f"{amplitudes[1]:.3f} / {amplitudes[2]:.3f} Mpc")
    print()
    print(f"{'Posição':<24} {'Incluídas':>10} "
          f"{'Excluídas':>10} {'Retidas':>10}")
    print("-" * 60)

    for nome, delta in deslocamentos:
        c = centro + np.asarray(delta, dtype=float)
        dentro = np.all(np.abs(pontos - c) <= L/2, axis=1)
        n_dentro = int(dentro.sum())
        n_fora = len(pontos) - n_dentro
        pct = 100 * n_dentro / len(pontos)

        print(f"{nome:<24} {n_dentro:10d} {n_fora:10d} "
              f"{pct:9.2f}%")

    print("\nNota: esta auditoria mede recorte geométrico, não periodicidade.")
    print("Nenhum CSV ou script original foi alterado.")


if __name__ == "__main__":
    main()
