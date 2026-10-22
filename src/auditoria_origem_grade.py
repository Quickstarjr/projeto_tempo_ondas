#!/usr/bin/env python3
"""Teste de origem, fase e estabilidade do pico FFT."""

import numpy as np


def analisar_origem(L=500.0, N=64, deslocamento=0.0):
    dx = L / N
    x = np.arange(N) * dx

    # Onda de 100 Mpc: exatamente cinco ciclos na caixa.
    k0 = 2 * np.pi / 100.0

    # Deslocar a origem equivale a mudar a fase da onda.
    campo = np.sin(k0 * (x + deslocamento))
    F = np.fft.fft(campo)
    P = np.abs(F) ** 2
    freq = 2 * np.pi * np.fft.fftfreq(N, d=dx)

    # Ignora o modo zero.
    P[0] = 0
    i = int(np.argmax(P))

    return {
        "deslocamento": deslocamento,
        "modo": int(round(freq[i] * L / (2 * np.pi))),
        "k": abs(freq[i]),
        "lambda": 2 * np.pi / abs(freq[i]),
        "potencia_pico": P[i],
    }


def main():
    L = 500.0
    deslocamentos = [0.0, 10.0, 25.0, 50.0, 125.0]

    print("=" * 65)
    print("AUDITORIA DE ORIGEM DA GRADE — GEPETO")
    print("=" * 65)
    print("Onda teórica: 100 Mpc | Caixa: 500 Mpc | Grade: 64")
    print()
    print(f"{'Desloc. (Mpc)':>14} {'Modo':>8} {'k (rad/Mpc)':>15} "
          f"{'Lambda (Mpc)':>15} {'Potência pico':>16}")

    resultados = []
    for deslocamento in deslocamentos:
        r = analisar_origem(deslocamento=deslocamento)
        resultados.append(r)
        print(f"{r['deslocamento']:14.1f} {r['modo']:8d} "
              f"{r['k']:15.6f} {r['lambda']:15.3f} "
              f"{r['potencia_pico']:16.3f}")

    lambdas = [r["lambda"] for r in resultados]
    estavel = np.allclose(lambdas, 100.0, atol=1e-9)

    print()
    print("RESULTADO:",
          "PASSOU — escala preservada." if estavel else
          "FALHOU — investigar a origem.")

    if not estavel:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
