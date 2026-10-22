#!/usr/bin/env python3
"""Permutação global usando grades angulares regulares deslocadas."""

from pathlib import Path
import argparse
import json
import time

import numpy as np
import pandas as pd

THRESHOLDS = [18.0, 18.5, 19.0, 19.5, 20.0, 21.0, 22.0]
Z_EDGES = [0.049, 0.06, 0.07, 0.08, 0.09, 0.10]
OFFSETS = [0.0, 0.25, 0.50, 0.75]
RA_CELLS = 4
DEC_CELLS = 3
MIN_CELL_N = 100


def build_grid(ra, dec, ra_offset, dec_offset):
    ra_min, ra_max = float(ra.min()), float(ra.max())
    dec_min, dec_max = float(dec.min()), float(dec.max())

    rw = (ra_max - ra_min) / RA_CELLS
    dw = (dec_max - dec_min) / DEC_CELLS

    ra_origin = ra_min + ra_offset * rw
    dec_origin = dec_min + dec_offset * dw

    ra_start = int(np.floor((ra_min - ra_origin) / rw))
    ra_stop = int(np.ceil((ra_max - ra_origin) / rw))
    dec_start = int(np.floor((dec_min - dec_origin) / dw))
    dec_stop = int(np.ceil((dec_max - dec_origin) / dw))

    ra_edges = ra_origin + np.arange(ra_start, ra_stop + 1) * rw
    dec_edges = dec_origin + np.arange(dec_start, dec_stop + 1) * dw

    ri = np.searchsorted(ra_edges, ra, side="right") - 1
    di = np.searchsorted(dec_edges, dec, side="right") - 1

    ri = np.clip(ri, 0, len(ra_edges) - 2)
    di = np.clip(di, 0, len(dec_edges) - 2)

    n_ra = len(ra_edges) - 1
    n_dec = len(dec_edges) - 1
    ids = di * n_ra + ri
    counts = np.bincount(ids, minlength=n_ra * n_dec)

    assert len(ids) == len(ra)
    assert counts.sum() == len(ra)

    return {
        "id": ids,
        "counts": counts,
        "eligible": counts >= MIN_CELL_N,
        "ra_offset": ra_offset,
        "dec_offset": dec_offset,
        "n_ra": n_ra,
        "n_dec": n_dec,
    }


def evaluate(magnitudes, grids):
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
        "auditoria_permutacao_global_grade_regular"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    required = ["ra", "dec", "z", "modelMag_r"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes: {missing}")

    df = df[required].replace([np.inf, -np.inf], np.nan).dropna()
    df = df[
        df["ra"].between(0, 360)
        & df["dec"].between(-90, 90)
    ].copy()

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

    grids = [
        build_grid(ra, dec, ro, do)
        for ro in OFFSETS
        for do in OFFSETS
    ]

    grid_report = []
    for g in grids:
        grid_report.append({
            "ra_offset": g["ra_offset"],
            "dec_offset": g["dec_offset"],
            "n_ra": g["n_ra"],
            "n_dec": g["n_dec"],
            "n_cells": len(g["counts"]),
            "n_occupied": int(np.sum(g["counts"] > 0)),
            "n_eligible": int(g["eligible"].sum()),
            "min_cell_count": int(g["counts"].min()),
            "max_cell_count": int(g["counts"].max()),
            "total_objects": int(g["counts"].sum()),
        })

    observed = evaluate(mag, grids)
    if not np.isfinite(observed["amplitude"]):
        raise RuntimeError("Não há células elegíveis suficientes.")

    strata = [
        np.flatnonzero(z_bin == b)
        for b in np.unique(z_bin)
    ]
    strata = [idx for idx in strata if len(idx) > 1]

    rng = np.random.default_rng(args.seed)
    null_maxima = np.empty(args.n_perm, dtype=float)

    print("=" * 70)
    print("PERMUTAÇÃO GLOBAL — GRADE REGULAR")
    print("=" * 70)
    print(f"Objetos analisados : {len(df):,}")
    print(f"Posições de grade  : {len(grids)}")
    print(f"Limiares           : {THRESHOLDS}")
    print(f"Mínimo por célula  : {MIN_CELL_N}")
    print(f"Permutações        : {args.n_perm:,}")
    print(f"Semente            : {args.seed}")
    print(f"Amplitude observada: {observed['amplitude'] * 100:.4f} p.p.")
    print("\nDistribuição nula em andamento...")

    t0 = time.time()
    for r in range(args.n_perm):
        permuted_mag = mag.copy()
        for idx in strata:
            permuted_mag[idx] = rng.permutation(mag[idx])

        null_maxima[r] = evaluate(permuted_mag, grids)["amplitude"]

        if (r + 1) % 250 == 0 or r + 1 == args.n_perm:
            print(f"  {r + 1:,}/{args.n_perm:,}", flush=True)

    p_value = (
        1 + np.count_nonzero(null_maxima >= observed["amplitude"])
    ) / (args.n_perm + 1)
    mc_se = np.sqrt(p_value * (1 - p_value) / (args.n_perm + 1))
    q50, q95, q99 = np.quantile(null_maxima, [0.50, 0.95, 0.99])

    print("\n=== RESULTADO GLOBAL ===")
    print(f"Limiar vencedor : > {observed['threshold']}")
    print(f"Grade RA/DEC    : {observed['ra_offset']:.2f} / "
          f"{observed['dec_offset']:.2f}")
    print(f"Células válidas : {observed['n_eligible_cells']}")
    print(f"Amplitude       : {observed['amplitude'] * 100:.4f} p.p.")
    print(f"Mediana nula    : {q50 * 100:.4f} p.p.")
    print(f"Percentil 95    : {q95 * 100:.4f} p.p.")
    print(f"Percentil 99    : {q99 * 100:.4f} p.p.")
    print(f"Valor-p global  : {p_value:.6f}")
    print(f"Erro MC aprox.  : {mc_se:.6f}")
    print(f"Tempo           : {time.time() - t0:.1f} s")

    pd.DataFrame({
        "permutacao": np.arange(1, args.n_perm + 1),
        "max_amplitude": null_maxima,
        "max_amplitude_pp": null_maxima * 100,
    }).to_csv(out_dir / "maximos_permutados.csv", index=False)

    pd.DataFrame(grid_report).to_csv(
        out_dir / "diagnostico_grades.csv", index=False
    )

    summary = {
        "input": str(input_path),
        "n_objects": int(len(df)),
        "thresholds": THRESHOLDS,
        "offsets": OFFSETS,
        "grid_positions": grid_report,
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
        "elapsed_seconds": float(time.time() - t0),
        "caveats": [
            "Teste exploratório; limiares e grades foram escolhidos após "
            "inspeção anterior dos dados.",
            "Permutação condicionada a faixas de redshift.",
            "Não controla máscara, completude, extinção ou qualidade "
            "fotométrica.",
            "RA/DEC retangular não representa células de área celeste igual.",
            "Um valor-p pequeno não demonstra uma onda cosmológica.",
        ],
    }
    with open(out_dir / "resumo.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nRelatórios salvos em: {out_dir}")


if __name__ == "__main__":
    main()
