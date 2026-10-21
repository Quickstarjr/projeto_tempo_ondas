#!/usr/bin/env python3
"""Curva de potência usando catálogos sintéticos novos e independentes."""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import mannwhitneyu

from auditoria_amplitude_espectro import (
    N_PARTICLES, BOX, GRID, WAVELENGTH, AXIS,
    gerar_catalogo_modulado, espectro_no_eixo,
)

AMPLITUDES = (0.0, 0.005, 0.01, 0.015, 0.02, 0.03, 0.05)
N_EXPERIMENTOS = 200
N_POR_GRUPO = 50
ALPHA = 0.05
SEED_MASTER = 2026102103

OUT_DIR = Path("outputs/reports/curva_potencia")
OUT_DIR.mkdir(parents=True, exist_ok=True)

rng_master = np.random.default_rng(SEED_MASTER)
seeds_usadas = set()
resultados = []
total_catalogos = 0


def gerar_potencia(amplitude, experimento, grupo, indice):
    global total_catalogos

    # Gera sementes únicas sem interromper o experimento
    # quando ocorre uma colisão aleatória.
    while True:
        seed = int(rng_master.integers(0, 2**32, dtype=np.uint64))
        if seed not in seeds_usadas:
            seeds_usadas.add(seed)
            break

    rng = np.random.default_rng(seed)
    pontos = gerar_catalogo_modulado(
        N_PARTICLES, BOX, WAVELENGTH, amplitude, rng, axis=AXIS
    )
    diag = espectro_no_eixo(pontos, BOX, GRID, axis=AXIS)
    total_catalogos += 1

    return {
        "experimento": experimento,
        "grupo": grupo,
        "indice": indice,
        "seed": seed,
        "amplitude": amplitude,
        "N_realizado": diag["N_realizado"],
        "P_mean_k3": float(diag["P_mean"]),
        "conjugado": bool(diag["conjugado"]),
    }


def wilson(k, n, z=1.959963984540054):
    p = k / n
    den = 1 + z*z/n
    centro = (p + z*z/(2*n)) / den
    margem = z * np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return max(0.0, centro-margem), min(1.0, centro+margem)


print("=== CURVA DE POTÊNCIA ===")
print(f"Amplitudes: {AMPLITUDES}")
print(f"Experimentos/amplitude: {N_EXPERIMENTOS}")
print(f"Catálogos/grupo: {N_POR_GRUPO}")
print(f"Total previsto: {len(AMPLITUDES)*N_EXPERIMENTOS*2*N_POR_GRUPO}")
print(f"Alpha: {ALPHA}\n")

for amplitude in AMPLITUDES:
    p_values = []

    for exp in range(N_EXPERIMENTOS):
        referencia = [
            gerar_potencia(0.0, exp, "referencia_nula", i)
            for i in range(N_POR_GRUPO)
        ]
        teste = [
            gerar_potencia(amplitude, exp, "grupo_teste", i)
            for i in range(N_POR_GRUPO)
        ]

        x = [r["P_mean_k3"] for r in referencia]
        y = [r["P_mean_k3"] for r in teste]

        p_value = float(mannwhitneyu(
            x, y, alternative="two-sided"
        ).pvalue)
        p_values.append(p_value)

        # Grava um registro por comparação.
        resultados.append({
            "amplitude": amplitude,
            "experimento": exp,
            "n_referencia": N_POR_GRUPO,
            "n_teste": N_POR_GRUPO,
            "p_value": p_value,
            "detectado": p_value < ALPHA,
        })

    detectados = int(np.sum(np.array(p_values) < ALPHA))
    n = len(p_values)
    lo, hi = wilson(detectados, n)

    print(
        f"A={amplitude:.3f} | potência/taxa FP={detectados/n:.3f} "
        f"({detectados}/{n}) | IC95%=[{lo:.3f}, {hi:.3f}]"
    )

    if amplitude == 0.0:
        print("  (A=0: taxa de falsos positivos neste ensaio)")

df = pd.DataFrame(resultados)
csv_path = OUT_DIR / "resultados_curva_potencia.csv"
df.to_csv(csv_path, index=False)

manifest = {
    "descricao": "Curva de potência por amplitude sintética",
    "seed_master": SEED_MASTER,
    "amplitudes": list(AMPLITUDES),
    "n_experimentos_por_amplitude": N_EXPERIMENTOS,
    "n_por_grupo": N_POR_GRUPO,
    "alpha": ALPHA,
    "N_PARTICLES": N_PARTICLES,
    "BOX": BOX,
    "GRID": GRID,
    "WAVELENGTH": WAVELENGTH,
    "AXIS": AXIS,
    "total_catalogos": total_catalogos,
    "seeds_unicas": len(seeds_usadas),
    "teste": "Mann-Whitney bilateral sobre P_mean_k3",
    "gerador": "auditoria_amplitude_espectro.gerar_catalogo_modulado",
    "estimador": "auditoria_amplitude_espectro.espectro_no_eixo",
}
(OUT_DIR / "manifesto.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8"
)

print("\n=== INTEGRIDADE ===")
print(f"Catálogos gerados: {total_catalogos}")
print(f"Sementes únicas: {len(seeds_usadas)}")
print(f"Amplitude zero na referência: sim")
print(f"Resultados: {csv_path}")
print(f"Manifesto: {OUT_DIR / 'manifesto.json'}")
print("[CONCLUÍDO]")
