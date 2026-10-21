#!/usr/bin/env python3
"""Estima a taxa de falsos positivos usando pares de amostras nulas novas."""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import mannwhitneyu

from auditoria_amplitude_espectro import (
    N_PARTICLES, BOX, GRID, WAVELENGTH, AXIS, K_SPECTRUM,
    gerar_catalogo_modulado, espectro_no_eixo,
)

N_EXPERIMENTOS = 100
N_POR_GRUPO = 50
ALPHA = 0.05
AMPLITUDE = 0.0
SEED_MASTER = 2026102101

OUT_DIR = Path("outputs/reports/taxa_falsos_positivos")
OUT_DIR.mkdir(parents=True, exist_ok=True)

rng_master = np.random.default_rng(SEED_MASTER)
resultados = []
registros = []
seeds_usadas = set()


def gerar_potencia_nula(experimento, grupo, indice):
    seed = int(rng_master.integers(0, 2**32 - 1))

    if seed in seeds_usadas:
        raise RuntimeError(f"Semente repetida detectada: {seed}")
    seeds_usadas.add(seed)

    rng = np.random.default_rng(seed)
    pontos = gerar_catalogo_modulado(
        N_PARTICLES, BOX, WAVELENGTH, AMPLITUDE, rng, axis=AXIS
    )
    diag = espectro_no_eixo(pontos, BOX, GRID, axis=AXIS)

    registros.append({
        "experimento": experimento,
        "grupo": grupo,
        "indice": indice,
        "seed": seed,
        "amplitude": AMPLITUDE,
        "N_realizado": diag["N_realizado"],
        "P_mean_k3": diag["P_mean"],
        "P_k3": diag["P_k"][3],
        "P_k6": diag["P_k"][6],
        "conjugado": diag["conjugado"],
    })
    return diag["P_mean"], diag["P_k"][6]


print("=== TESTE DE TAXA DE FALSOS POSITIVOS ===")
print(f"Experimentos: {N_EXPERIMENTOS}")
print(f"Catálogos por grupo: {N_POR_GRUPO}")
print(f"Catálogos previstos: {N_EXPERIMENTOS * N_POR_GRUPO * 2}")
print(f"Alpha: {ALPHA}")
print("Todos os catálogos terão amplitude zero.\n")

for exp in range(N_EXPERIMENTOS):
    ref_k3, ref_k6 = [], []
    teste_k3, teste_k6 = [], []

    for i in range(N_POR_GRUPO):
        a, b = gerar_potencia_nula(exp, "referencia", i)
        ref_k3.append(a)
        ref_k6.append(b)

    for i in range(N_POR_GRUPO):
        a, b = gerar_potencia_nula(exp, "teste", i)
        teste_k3.append(a)
        teste_k6.append(b)

    p_k3 = float(mannwhitneyu(
        ref_k3, teste_k3, alternative="two-sided"
    ).pvalue)

    p_k6 = float(mannwhitneyu(
        ref_k6, teste_k6, alternative="two-sided"
    ).pvalue)

    resultados.append({
        "experimento": exp,
        "n_referencia": N_POR_GRUPO,
        "n_teste": N_POR_GRUPO,
        "p_k3": p_k3,
        "falso_positivo_k3": p_k3 < ALPHA,
        "p_k6": p_k6,
        "falso_positivo_k6": p_k6 < ALPHA,
    })

    if (exp + 1) % 10 == 0:
        print(f"[OK] {exp + 1}/{N_EXPERIMENTOS}")

df = pd.DataFrame(resultados)
df_catalogos = pd.DataFrame(registros)

# Intervalo de Wilson de 95% para a proporção observada.
def intervalo_wilson(k, n, z=1.959963984540054):
    p = k / n
    den = 1 + z*z/n
    centro = (p + z*z/(2*n)) / den
    margem = z * np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return max(0.0, centro - margem), min(1.0, centro + margem)

def resumir(coluna):
    k = int(df[coluna].sum())
    n = len(df)
    lo, hi = intervalo_wilson(k, n)
    return k, n, k/n, lo, hi

csv_tests = OUT_DIR / "resultados_experimentos.csv"
csv_catalogos = OUT_DIR / "catalogos_gerados.csv"
manifest_path = OUT_DIR / "manifesto.json"

df.to_csv(csv_tests, index=False)
df_catalogos.to_csv(csv_catalogos, index=False)

k3 = resumir("falso_positivo_k3")
k6 = resumir("falso_positivo_k6")

manifest = {
    "descricao": "Taxa de falsos positivos com comparações nulas independentes",
    "seed_master": SEED_MASTER,
    "n_experimentos": N_EXPERIMENTOS,
    "n_por_grupo": N_POR_GRUPO,
    "amplitude": AMPLITUDE,
    "alpha": ALPHA,
    "N_PARTICLES": N_PARTICLES,
    "BOX": BOX,
    "GRID": GRID,
    "WAVELENGTH": WAVELENGTH,
    "AXIS": AXIS,
    "K_SPECTRUM": list(K_SPECTRUM),
    "total_catalogos": len(df_catalogos),
    "seeds_unicas": int(df_catalogos["seed"].nunique()),
    "gerador": "auditoria_amplitude_espectro.gerar_catalogo_modulado",
    "estimador": "auditoria_amplitude_espectro.espectro_no_eixo",
    "teste_primario": "Mann-Whitney bilateral em P_mean_k3",
    "teste_secundario_exploratorio": "Mann-Whitney bilateral em P_k6",
    "intervalo": "Wilson 95%",
}
manifest_path.write_text(
    json.dumps(manifest, indent=2), encoding="utf-8"
)

print("\n=== RESULTADO PRIMÁRIO: P_mean_k3 ===")
print(f"Falsos positivos: {k3[0]}/{k3[1]}")
print(f"Taxa observada: {100*k3[2]:.2f}%")
print(f"IC Wilson 95%: [{100*k3[3]:.2f}%, {100*k3[4]:.2f}%]")

print("\n=== DIAGNÓSTICO SECUNDÁRIO: P_k6 ===")
print(f"Falsos positivos: {k6[0]}/{k6[1]}")
print(f"Taxa observada: {100*k6[2]:.2f}%")
print(f"IC Wilson 95%: [{100*k6[3]:.2f}%, {100*k6[4]:.2f}%]")

print("\n=== INTEGRIDADE ===")
print(f"Catálogos registrados: {len(df_catalogos)}")
print(f"Sementes únicas: {df_catalogos['seed'].nunique()}")
print(f"Amplitude única: {df_catalogos['amplitude'].unique().tolist()}")
print(f"N realizado: {df_catalogos['N_realizado'].unique().tolist()}")
print(f"Conjugação: {int(df_catalogos['conjugado'].sum())}/{len(df_catalogos)}")

print("\nArquivos:")
print(csv_tests)
print(csv_catalogos)
print(manifest_path)
print("\n[CONCLUÍDO]")
