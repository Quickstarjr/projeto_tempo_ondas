#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, binomtest

from teste_orientacao_xyz import (
    N_PARTICLES, BOX, GRID, WAVELENGTH,
    AXIS_NAMES, gerar_catalogo_modulado,
    medir_potencia_eixos, semente_unica,
)

LOTES = 100
REPS_POR_LOTE = 200
ALPHA = 0.05

PASTA = Path("outputs/reports/calibracao_falsos_positivos_xyz")


def holm(p_values):
    p = np.asarray(p_values, dtype=float)
    ordem = np.argsort(p)
    ajustados = np.empty(len(p))
    maior = 0.0

    for rank, i in enumerate(ordem):
        maior = max(maior, min(1.0, (len(p) - rank) * p[i]))
        ajustados[i] = maior

    return ajustados


def testar(a, b):
    diferenca = np.asarray(a) - np.asarray(b)

    if np.allclose(diferenca, 0):
        return 1.0

    return float(wilcoxon(a, b, alternative="two-sided").pvalue)


def main():
    PASTA.mkdir(parents=True, exist_ok=True)
    resultados = []

    for lote in range(LOTES):
        potencias = {"X": [], "Y": [], "Z": []}

        for rep in range(REPS_POR_LOTE):
            seed = semente_unica("calibracao_nula", lote, rep)
            rng = np.random.default_rng(seed)

            pontos = gerar_catalogo_modulado(
                N_PARTICLES, BOX, WAVELENGTH,
                0.0, rng, axis=0
            )
            medida = medir_potencia_eixos(
                pontos, BOX, GRID, WAVELENGTH
            )

            for eixo in AXIS_NAMES.values():
                potencias[eixo].append(medida[f"P_{eixo}"])

        pares = [("X", "Y"), ("X", "Z"), ("Y", "Z")]
        ps = [testar(potencias[a], potencias[b]) for a, b in pares]
        ps_holm = holm(ps)

        linha = {"lote": lote}
        for i, (a, b) in enumerate(pares):
            linha[f"p_{a}_{b}"] = ps[i]
            linha[f"p_holm_{a}_{b}"] = ps_holm[i]

        linha["rejeicao_familiar"] = bool(
            np.any(ps_holm < ALPHA)
        )
        resultados.append(linha)

        print(
            f"Lote {lote + 1:02d}/{LOTES}: "
            f"p={np.round(ps, 4)} | "
            f"algum Holm significativo="
            f"{linha['rejeicao_familiar']}"
        )

    df = pd.DataFrame(resultados)
    destino = PASTA / "resultados_lotes.csv"
    df.to_csv(destino, index=False)

    print("\n=== CALIBRAÇÃO NULA ===")
    for a, b in [("X", "Y"), ("X", "Z"), ("Y", "Z")]:
        taxa = (df[f"p_{a}_{b}"] < ALPHA).mean()
        print(f"Falso positivo {a}-{b}: {taxa:.1%} ({int((df[f'p_{a}_{b}'] < ALPHA).sum())}/{LOTES})")

    rejeicoes = int(df["rejeicao_familiar"].sum())
    taxa_familiar = rejeicoes / LOTES
    intervalo = binomtest(
        rejeicoes, LOTES
    ).proportion_ci(confidence_level=0.95)

    print(
        f"Erro familiar após Holm: {taxa_familiar:.1%} "
        f"({rejeicoes}/{LOTES})"
    )
    print(
        "IC 95% binomial para erro familiar: "
        f"[{intervalo.low:.1%}, {intervalo.high:.1%}]"
    )
    print(f"Arquivo: {destino}")
    print("Nota: 20 lotes constituem um piloto; a incerteza ainda será grande.")


if __name__ == "__main__":
    main()
