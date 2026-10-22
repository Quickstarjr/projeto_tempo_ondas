#!/usr/bin/env python3
"""Teste global de permutação: cauda de magnitude x posição da grade.

O teste permuta modelMag_r dentro de faixas de redshift, preservando
as posições celestes e a distribuição de magnitudes de cada faixa.

A estatística global é a maior amplitude (maior taxa - menor taxa)
entre todos os limiares e deslocamentos de grade.

Resultado exploratório: não comprova uma estrutura cosmológica.
"""

from pathlib import Path
import argparse
import json
import time

import numpy as np
import pandas as pd


THRESHOLDS = [18.0, 18.5, 19.0, 19.5, 20.0, 21.0, 22.0]
Z_EDGES = [0.049, 0.06, 0.07, 0.08, 0.09, 0.10]
RA_CELLS = 4
DEC_CELLS = 3
OFFSETS = [0.0, 0.25, 0.50, 0.75]
MIN_CELL_N = 100


def build_grid(ra, dec, ra_offset, dec_offset):
    """Cria partições deslocadas mantendo todos os pontos no campo."""
    ra_min, ra_max = float(ra.min()), float(ra.max())
    dec_min, dec_max = float(dec.min()), float(dec.max())

    ra_width = (ra_max - ra_min) / RA_CELLS
    dec_width = (dec_max - dec_min) / DEC_CELLS

    # As bordas externas ficam fixas. Só as divisões internas se deslocam.
    ra_cuts = [
        ra_min + (j + ra_offset) * ra_width
        for j in range(1, RA_CELLS)
    ]
    dec_cuts = [
        dec_min + (j + dec_offset) * dec_width
        for j in range(1, DEC_CELLS)
    ]

    ra_cuts = sorted(x for x in ra_cuts if ra_min < x < ra_max)
    dec_cuts = sorted(x for x in dec_cuts if dec_min < x < dec_max)

    ra_edges = np.array([ra_min, *ra_cuts, ra_max])
    dec_edges = np.array([dec_min, *dec_cuts, dec_max])

    # searchsorted garante que cada ponto pertença a uma única célula.
    ri = np.searchsorted(ra_edges[1:-1], ra, side="right")
    di = np.searchsorted(dec_edges[1:-1], dec, side="right")
    n_ra = len(ra_edges) - 1
    n_dec = len(dec_edges) - 1
    cell_id = di * n_ra + ri
    n_cells = n_ra * n_dec

    counts = np.bincount(cell_id, minlength=n_cells)
    return {
        "id": cell_id,
        "counts": counts,
        "eligible": counts >= MIN_CELL_N,
        "ra_offset": ra_offset,
        "dec_offset": dec_offset,
        "n_ra": n_ra,
        "n_dec": n_dec,
        "ra_edges": ra_edges,
        "dec_edges": dec_edges,
    }


def evaluate(magnitudes, grids):
    """Retorna o máximo global e o melhor caso para esta realização."""
    best = {
        "amplitude": -np.inf,
        "threshold": None,
        "ra_offset": None,
        "dec_offset": None,
        "min_rate": None,
        "max_rate": None,
        "n_eligible_cells": None,
    }

    for threshold in THRESHOLDS:
        tail = magnitudes > threshold

        for grid in grids:
            counts = grid["counts"]
            eligible = grid["eligible"]

            if eligible.sum() < 2:
                continue

            tail_counts = np.bincount(
                grid["id"][tail], minlength=len(counts)
            )
            rates = tail_counts[eligible] / counts[eligible]
            amplitude = float(rates.max() - rates.min())

            if amplitude > best["amplitude"]:
                best = {
                    "amplitude": amplitude,
                    "threshold": threshold,
                    "ra_offset": grid["ra_offset"],
                    "dec_offset": grid["dec_offset"],
                    "min_rate": float(rates.min()),
                    "max_rate": float(rates.max()),
                    "n_eligible_cells": int(eligible.sum()),
                }

    return best


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="outputs/reports/galaxias_tamanho/dados.csv",
    )
    parser.add_argument("--n-perm", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()

    if args.n_perm < 1:
        parser.error("--n-perm precisa ser >= 1")

    input_path = Path(args.input)
    out_dir = Path(
        "outputs/reports/galaxias_tamanho/"
        "auditoria_permutacao_global_cauda"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    required = ["ra", "dec", "z", "modelMag_r"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes: {missing}")

    df = df[required].replace([np.inf, -np.inf], np.nan).dropna().copy()
    df = df[
        (df["ra"] >= 0) & (df["ra"] <= 360)
        & (df["dec"] >= -90) & (df["dec"] <= 90)
    ].copy()

    # Reproduz as cinco faixas de redshift usadas na análise anterior.
    df["z_bin"] = pd.cut(
        df["z"],
        bins=Z_EDGES,
        right=True,
        include_lowest=True,
        labels=False,
    )
    df = df.dropna(subset=["z_bin"]).copy()
    df["z_bin"] = df["z_bin"].astype(int)

    ra = df["ra"].to_numpy(float)
    dec = df["dec"].to_numpy(float)
    mag = df["modelMag_r"].to_numpy(float)
    z_bin = df["z_bin"].to_numpy(int)

    rng = np.random.default_rng(args.seed)

    # 4 x 4 posições de grade; cada posição é usada em dados e permutações.
    grids = [
        build_grid(ra, dec, ro, do)
        for ro in OFFSETS
        for do in OFFSETS
    ]

    if not grids:
        raise RuntimeError("Nenhuma grade foi criada.")

    observed = evaluate(mag, grids)
    if not np.isfinite(observed["amplitude"]):
        raise RuntimeError("Não há células elegíveis suficientes.")

    # Cada faixa de z mantém exatamente seus valores de magnitude;
    # apenas a associação entre magnitude e posição é quebrada.
    strata = [np.flatnonzero(z_bin == b) for b in np.unique(z_bin)]
    strata = [idx for idx in strata if len(idx) > 1]

    null_maxima = np.empty(args.n_perm, dtype=float)
    t0 = time.time()

    print("=" * 72)
    print("PERMUTAÇÃO GLOBAL — CAUDA DE MAGNITUDE E GRADE ANGULAR")
    print("=" * 72)
    print(f"Arquivo                 : {input_path}")
    print(f"Galáxias analisadas     : {len(df):,}")
    print(f"Faixas de redshift      : {len(np.unique(z_bin))}")
    print(f"Limiares                : {THRESHOLDS}")
    print(f"Posições de grade       : {len(grids)}")
    print(f"Células mínimas         : {MIN_CELL_N} objetos")
    print(f"Permutações             : {args.n_perm:,}")
    print(f"Semente                 : {args.seed}")
    print("\nCalculando distribuição nula...")

    for r in range(args.n_perm):
        permuted_mag = mag.copy()

        for idx in strata:
            permuted_mag[idx] = rng.permutation(mag[idx])

        null_maxima[r] = evaluate(permuted_mag, grids)["amplitude"]

        if (r + 1) % 500 == 0 or r + 1 == args.n_perm:
            print(f"  {r + 1:>6,}/{args.n_perm:,}", end="\r", flush=True)

    print()
    p_value = (
        1 + np.count_nonzero(null_maxima >= observed["amplitude"])
    ) / (args.n_perm + 1)

    mc_se = np.sqrt(p_value * (1 - p_value) / (args.n_perm + 1))
    q50, q95, q99 = np.quantile(null_maxima, [0.50, 0.95, 0.99])

    print("\n=== RESULTADO GLOBAL ===")
    print(f"Amplitude global observada : {observed['amplitude'] * 100:.4f} p.p.")
    print(f"Limiar do melhor caso      : > {observed['threshold']}")
    print(f"Deslocamento RA            : {observed['ra_offset']:.2f}")
    print(f"Deslocamento DEC           : {observed['dec_offset']:.2f}")
    print(f"Células elegíveis          : {observed['n_eligible_cells']}")
    print(f"Menor taxa no melhor caso  : {observed['min_rate'] * 100:.4f}%")
    print(f"Maior taxa no melhor caso  : {observed['max_rate'] * 100:.4f}%")
    print("\n=== MÁXIMOS SIMULADOS ===")
    print(f"Mediana                    : {q50 * 100:.4f} p.p.")
    print(f"Percentil 95               : {q95 * 100:.4f} p.p.")
    print(f"Percentil 99               : {q99 * 100:.4f} p.p.")
    print(f"Valor-p global              : {p_value:.6f}")
    print(f"Erro Monte Carlo aprox.     : {mc_se:.6f}")
    print(f"Tempo                      : {time.time() - t0:.1f} s")

    pd.DataFrame({
        "permutacao": np.arange(1, args.n_perm + 1),
        "max_amplitude": null_maxima,
        "max_amplitude_pp": null_maxima * 100,
    }).to_csv(out_dir / "maximos_permutados.csv", index=False)

    summary = {
        "input": str(input_path),
        "n_objects": int(len(df)),
        "thresholds": THRESHOLDS,
        "n_grid_positions": len(grids),
        "offsets": OFFSETS,
        "min_cell_n": MIN_CELL_N,
        "n_permutations": args.n_perm,
        "seed": args.seed,
        "observed_global": observed,
        "null_median": float(q50),
        "null_q95": float(q95),
        "null_q99": float(q99),
        "global_p_value": float(p_value),
        "monte_carlo_se_approx": float(mc_se),
        "strata_sizes": [int(len(idx)) for idx in strata],
        "caveats": [
            "Teste exploratório; limiares e grades foram escolhidos após "
            "inspeção anterior dos dados.",
            "Permutação condicionada a faixas de redshift; não controla "
            "máscara, completude, extinção ou qualidade fotométrica.",
            "A grade é uma partição angular retangular, não uma área "
            "celeste uniforme.",
            "Um valor-p pequeno não demonstra uma onda cosmológica."
        ],
    }
    with open(out_dir / "resumo.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nRelatórios salvos em: {out_dir}")
    print("Arquivos: maximos_permutados.csv e resumo.json")


if __name__ == "__main__":
    main()
