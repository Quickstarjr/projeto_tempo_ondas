
#!/usr/bin/env python3
"""Compara a grade completa com uma grade sem células externas."""

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


def build_grid(ra, dec, ro, do):
    ra_min, ra_max = float(ra.min()), float(ra.max())
    dec_min, dec_max = float(dec.min()), float(dec.max())

    rw = (ra_max - ra_min) / RA_CELLS
    dw = (dec_max - dec_min) / DEC_CELLS

    ra_origin = ra_min + ro * rw
    dec_origin = dec_min + do * dw

    rs = int(np.floor((ra_min - ra_origin) / rw))
    re = int(np.ceil((ra_max - ra_origin) / rw))
    ds = int(np.floor((dec_min - dec_origin) / dw))
    de = int(np.ceil((dec_max - dec_origin) / dw))

    ra_edges = ra_origin + np.arange(rs, re + 1) * rw
    dec_edges = dec_origin + np.arange(ds, de + 1) * dw

    ri = np.searchsorted(ra_edges, ra, side="right") - 1
    di = np.searchsorted(dec_edges, dec, side="right") - 1

    n_ra = len(ra_edges) - 1
    n_dec = len(dec_edges) - 1
    ri = np.clip(ri, 0, n_ra - 1)
    di = np.clip(di, 0, n_dec - 1)

    ids = di * n_ra + ri
    counts = np.bincount(ids, minlength=n_ra * n_dec)

    rows = np.repeat(np.arange(n_dec), n_ra)
    cols = np.tile(np.arange(n_ra), n_dec)

    # Exclui a primeira e última linha e coluna da grade.
    interior = (
        (rows > 0) & (rows < n_dec - 1)
        & (cols > 0) & (cols < n_ra - 1)
    )
    eligible_all = counts >= MIN_CELL_N
    eligible_inner = eligible_all & interior

    assert len(ids) == len(ra)
    assert counts.sum() == len(ra)

    return {
        "id": ids,
        "counts": counts,
        "all": eligible_all,
        "inner": eligible_inner,
        "ra_offset": ro,
        "dec_offset": do,
        "n_ra": n_ra,
        "n_dec": n_dec,
        "n_inner_eligible": int(eligible_inner.sum()),
        "n_all_eligible": int(eligible_all.sum()),
    }


def evaluate(mag, grids, mask_name):
    best = {
        "amplitude": -np.inf,
        "threshold": None,
        "ra_offset": None,
        "dec_offset": None,
        "min_rate": None,
        "max_rate": None,
        "n_eligible_cells": 0,
    }

    for threshold in THRESHOLDS:
        tail = mag > threshold

        for g in grids:
            eligible = g[mask_name]
            counts = g["counts"]

            if eligible.sum() < 2:
                continue

            tail_counts = np.bincount(
                g["id"][tail], minlength=len(counts)
            )
            rates = tail_counts[eligible] / counts[eligible]
            amplitude = float(rates.max() - rates.min())

            if amplitude > best["amplitude"]:
                best = {
                    "amplitude": amplitude,
                    "threshold": threshold,
                    "ra_offset": g["ra_offset"],
                    "dec_offset": g["dec_offset"],
                    "min_rate": float(rates.min()),
                    "max_rate": float(rates.max()),
                    "n_eligible_cells": int(eligible.sum()),
                }

    return best


def summarize(null, observed, n_perm):
    p = (1 + np.count_nonzero(null >= observed["amplitude"])) / (
        n_perm + 1
    )
    q50, q95, q99 = np.quantile(null, [0.50, 0.95, 0.99])

    return {
        "observed": observed,
        "null_median": float(q50),
        "null_q95": float(q95),
        "null_q99": float(q99),
        "global_p_value": float(p),
        "mc_se_approx": float(np.sqrt(p * (1 - p) / (n_perm + 1))),
        "n_null_ge_observed": int(
            np.count_nonzero(null >= observed["amplitude"])
        ),
    }


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

    out_dir = Path(
        "outputs/reports/galaxias_tamanho/auditoria_grade_sem_bordas"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)
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
        df["z"], bins=Z_EDGES, right=True,
        include_lowest=True, labels=False
    )
    df = df.dropna(subset=["z_bin"]).copy()
    df["z_bin"] = df["z_bin"].astype(int)

    ra = df["ra"].to_numpy(float)
    dec = df["dec"].to_numpy(float)
    mag = df["modelMag_r"].to_numpy(float)
    z_bin = df["z_bin"].to_numpy(int)

    grids = [
        build_grid(ra, dec, ro, do)
        for ro in OFFSETS for do in OFFSETS
    ]

    report = []
    for g in grids:
        report.append({
            "ra_offset": g["ra_offset"],
            "dec_offset": g["dec_offset"],
            "n_ra": g["n_ra"],
            "n_dec": g["n_dec"],
            "n_all_eligible": g["n_all_eligible"],
            "n_inner_eligible": g["n_inner_eligible"],
            "total_objects": int(g["counts"].sum()),
        })

    observed_all = evaluate(mag, grids, "all")
    observed_inner = evaluate(mag, grids, "inner")

    if not np.isfinite(observed_inner["amplitude"]):
        raise RuntimeError(
            "Não há pelo menos duas células interiores elegíveis."
        )

    strata = [
        np.flatnonzero(z_bin == b)
        for b in np.unique(z_bin)
    ]
    strata = [idx for idx in strata if len(idx) > 1]

    rng = np.random.default_rng(args.seed)
    null_all = np.empty(args.n_perm)
    null_inner = np.empty(args.n_perm)

    print("=" * 68)
    print("AUDITORIA: GRADE COMPLETA VS. SEM BORDAS")
    print("=" * 68)
    print(f"Objetos: {len(df):,}")
    print(f"Permutações: {args.n_perm:,}")
    print(f"Semente: {args.seed}")
    print("Células de borda: primeira/última linha e coluna")
    print("Calculando distribuição nula...")

    t0 = time.time()
    for r in range(args.n_perm):
        perm_mag = mag.copy()
        for idx in strata:
            perm_mag[idx] = rng.permutation(mag[idx])

        null_all[r] = evaluate(perm_mag, grids, "all")["amplitude"]
        null_inner[r] = evaluate(perm_mag, grids, "inner")["amplitude"]

        if (r + 1) % 250 == 0 or r + 1 == args.n_perm:
            print(f"  {r + 1:,}/{args.n_perm:,}", flush=True)

    result = {
        "input": args.input,
        "n_objects": int(len(df)),
        "n_permutations": args.n_perm,
        "seed": args.seed,
        "thresholds": THRESHOLDS,
        "offsets": OFFSETS,
        "min_cell_n": MIN_CELL_N,
        "border_definition": (
            "Exclui primeira e última linha e coluna de cada grade; "
            "mantém somente células com N >= MIN_CELL_N."
        ),
        "all_cells": summarize(null_all, observed_all, args.n_perm),
        "interior_only": summarize(
            null_inner, observed_inner, args.n_perm
        ),
        "grids": report,
        "elapsed_seconds": time.time() - t0,
        "caveats": [
            "Análise exploratória; parâmetros foram examinados previamente.",
            "Permutação das magnitudes dentro de estratos de redshift.",
            "A máscara real do levantamento e a completude não são conhecidas.",
            "Excluir bordas da grade não equivale a corrigir a máscara do céu.",
            "RA/DEC retangular não representa áreas esféricas iguais.",
            "Valor-p não demonstra uma onda cosmológica.",
        ],
    }

    with open(out_dir / "resumo.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    pd.DataFrame(report).to_csv(
        out_dir / "diagnostico_grades.csv", index=False
    )
    pd.DataFrame({
        "permutacao": np.arange(1, args.n_perm + 1),
        "max_completo_pp": null_all * 100,
        "max_interior_pp": null_inner * 100,
    }).to_csv(out_dir / "maximos_permutados.csv", index=False)

    for name in ("all_cells", "interior_only"):
        s = result[name]
        o = s["observed"]
        print(f"\n=== {name} ===")
        print(f"Amplitude: {o['amplitude'] * 100:.4f} p.p.")
        print(f"Limiar vencedor: > {o['threshold']}")
        print(f"Offsets RA/DEC: {o['ra_offset']} / {o['dec_offset']}")
        print(f"Células elegíveis: {o['n_eligible_cells']}")
        print(f"Mediana nula: {s['null_median'] * 100:.4f} p.p.")
        print(f"Percentil 95: {s['null_q95'] * 100:.4f} p.p.")
        print(f"Percentil 99: {s['null_q99'] * 100:.4f} p.p.")
        print(f"Máximos nulos >= observado: {s['n_null_ge_observed']}")
        print(f"Valor-p global: {s['global_p_value']:.6f}")
        print(f"Erro MC aprox.: {s['mc_se_approx']:.6f}")

    print(f"\nTempo: {result['elapsed_seconds']:.1f} s")
    print(f"Relatórios: {out_dir}")


if __name__ == "__main__":
    main()
