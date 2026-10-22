#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de orientação XYZ — Projeto Tempo, Ondas e Observador.

Objetivos:
1. Medir o falso positivo entre eixos com amplitude A=0.
2. Injetar uma modulação conhecida separadamente em X, Y e Z.
3. Verificar se a potência responde ao eixo correto.
4. Registrar sementes, dados individuais, resumos e manifesto.

Este teste usa catálogos sintéticos. Não constitui evidência cosmológica.
"""

import json
import hashlib
import platform
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

# Parâmetros compatíveis com as auditorias anteriores.
N_PARTICLES = 12000
BOX = 300.0
GRID = 64
WAVELENGTH = 100.0
AMPLITUDE = 0.10
REPS = 200
ALPHA = 0.05
SEED_MASTER = 20261022

AXES = (0, 1, 2)
AXIS_NAMES = {0: "X", 1: "Y", 2: "Z"}
OUTPUT_DIR = Path("outputs/reports/orientacao_xyz")


def gerar_catalogo_modulado(n, box, wavelength, amplitude, rng, axis=0):
    """Mesmo método de amostragem por rejeição das auditorias anteriores."""
    if not 0 <= amplitude < 1:
        raise ValueError("Amplitude deve estar em [0, 1).")
    if axis not in AXES:
        raise ValueError("axis deve ser 0 (X), 1 (Y) ou 2 (Z).")
    if box <= 0 or wavelength <= 0 or n <= 0:
        raise ValueError("n, box e wavelength devem ser positivos.")

    pts = np.empty((n, 3), dtype=np.float64)
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


def medir_potencia_eixos(points, box, grid_n, wavelength):
    """
    Mede P_mean no modo axial mais próximo do k-alvo, em X, Y e Z.
    Preserva a janela Hann 3D e a definição de potência das auditorias.
    """
    hist, _ = np.histogramdd(
        points,
        bins=(grid_n, grid_n, grid_n),
        range=((0, box), (0, box), (0, box)),
    )
    field = hist.astype(np.float64) - hist.mean()

    win1 = np.hanning(grid_n)
    window = (
        win1[:, None, None]
        * win1[None, :, None]
        * win1[None, None, :]
    )
    field *= window

    power = np.abs(np.fft.fftn(field)) ** 2
    freq = np.fft.fftfreq(grid_n, d=box / grid_n) * 2 * np.pi
    k_target = 2 * np.pi / wavelength

    idx_pos = int(np.argmin(np.abs(freq - k_target)))
    idx_neg = int(np.argmin(np.abs(freq + k_target)))
    conjugado = ((idx_pos + idx_neg) % grid_n) == 0

    resultado = {
        "pos_idx": idx_pos,
        "neg_idx": idx_neg,
        "conjugado": bool(conjugado),
        "N_realizado": int(len(points)),
    }

    for axis, nome in AXIS_NAMES.items():
        indices = [0, 0, 0]
        indices[axis] = idx_pos
        p_pos = float(power[tuple(indices)])
        indices[axis] = idx_neg
        p_neg = float(power[tuple(indices)])

        resultado[f"P_{nome}_pos"] = p_pos
        resultado[f"P_{nome}_neg"] = p_neg
        resultado[f"P_{nome}"] = 0.5 * (p_pos + p_neg)

    return resultado


def semente_unica(*partes):
    """Semente determinística independente da ordem de execução."""
    payload = ":".join(map(str, (SEED_MASTER,) + partes)).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "little") % (2**32)


def comparar_grupos(a, b):
    """Mann–Whitney bilateral para grupos independentes."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]

    if len(a) < 2 or len(b) < 2:
        return {"n_a": len(a), "n_b": len(b), "mediana_a": np.nan,
                "mediana_b": np.nan, "diferenca_mediana": np.nan,
                "p": np.nan}

    teste = mannwhitneyu(a, b, alternative="two-sided")
    return {
        "n_a": int(len(a)),
        "n_b": int(len(b)),
        "mediana_a": float(np.median(a)),
        "mediana_b": float(np.median(b)),
        "diferenca_mediana": float(np.median(a) - np.median(b)),
        "p": float(teste.pvalue),
    }


def comparar_pareado(a, b):
    """Wilcoxon pareado para medidas de eixos do mesmo catálogo."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    dif = a - b

    if len(dif) < 2:
        p = np.nan
    elif np.allclose(dif, 0):
        p = 1.0
    else:
        p = float(wilcoxon(a, b, alternative="two-sided").pvalue)

    return {
        "n_pares": int(len(dif)),
        "media_diferenca": float(np.mean(dif)) if len(dif) else np.nan,
        "mediana_diferenca": float(np.median(dif)) if len(dif) else np.nan,
        "p": p,
    }


def rodar_experimento():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    linhas = []

    # Controle nulo e três orientações do sinal.
    condicoes = [
        ("nulo", 0.0, None),
        ("sinal", AMPLITUDE, 0),
        ("sinal", AMPLITUDE, 1),
        ("sinal", AMPLITUDE, 2),
    ]

    for condicao, amplitude, eixo_injetado in condicoes:
        for rep in range(REPS):
            seed = semente_unica(condicao, amplitude, eixo_injetado, rep)
            rng = np.random.default_rng(seed)

            # No nulo, axis não altera a densidade; usamos axis=0 por convenção.
            axis_geracao = 0 if eixo_injetado is None else eixo_injetado
            pontos = gerar_catalogo_modulado(
                N_PARTICLES, BOX, WAVELENGTH, amplitude, rng,
                axis=axis_geracao,
            )
            medicao = medir_potencia_eixos(
                pontos, BOX, GRID, WAVELENGTH
            )

            linhas.append({
                "condicao": condicao,
                "amplitude": amplitude,
                "eixo_injetado": (
                    "nenhum" if eixo_injetado is None
                    else AXIS_NAMES[eixo_injetado]
                ),
                "rep": rep,
                "seed": seed,
                **medicao,
            })

        print(
            f"[OK] {condicao}, A={amplitude:.3f}, "
            f"eixo={eixo_injetado}, n={REPS}"
        )

    df = pd.DataFrame(linhas)
    df.to_csv(OUTPUT_DIR / "realizacoes_xyz.csv", index=False)

    # Teste 1: fundo nulo. As três medidas de cada linha pertencem
    # ao mesmo catálogo, portanto as comparações são pareadas.
    nulo = df[df["condicao"] == "nulo"]
    resumo_nulo = []
    for a, b in ((("X", "Y")), (("X", "Z")), (("Y", "Z"))):
        r = comparar_pareado(nulo[f"P_{a}"], nulo[f"P_{b}"])
        resumo_nulo.append({
            "teste": "nulo_pareado",
            "eixo_a": a,
            "eixo_b": b,
            **r,
        })

    # Teste 2: em cada injeção, comparamos os eixos medidos
    # no mesmo catálogo: comparação pareada.
    resumo_sinal = []
    for eixo in AXIS_NAMES.values():
        sub = df[
            (df["condicao"] == "sinal")
            & (df["eixo_injetado"] == eixo)
        ]
        for outro in AXIS_NAMES.values():
            if outro == eixo:
                continue
            r = comparar_pareado(sub[f"P_{eixo}"], sub[f"P_{outro}"])
            resumo_sinal.append({
                "eixo_injetado": eixo,
                "eixo_sinal": eixo,
                "eixo_comparacao": outro,
                **r,
            })

    # Teste 3: cada eixo injetado contra o fundo nulo.
    # Catálogos independentes: Mann–Whitney, não teste pareado.
    resumo_fundo = []
    for eixo in AXIS_NAMES.values():
        sub = df[
            (df["condicao"] == "sinal")
            & (df["eixo_injetado"] == eixo)
        ]
        for medido in AXIS_NAMES.values():
            r = comparar_grupos(sub[f"P_{medido}"], nulo[f"P_{medido}"])
            resumo_fundo.append({
                "eixo_injetado": eixo,
                "eixo_medido": medido,
                **r,
            })

    pd.DataFrame(resumo_nulo).to_csv(
        OUTPUT_DIR / "resumo_nulo.csv", index=False
    )
    pd.DataFrame(resumo_sinal).to_csv(
        OUTPUT_DIR / "resumo_sinal.csv", index=False
    )
    pd.DataFrame(resumo_fundo).to_csv(
        OUTPUT_DIR / "comparacoes_com_nulo.csv", index=False
    )

    manifesto = {
        "experimento": "orientacao_xyz",
        "status": "sintetico; não constitui evidência cosmológica",
        "N_PARTICLES": N_PARTICLES,
        "BOX": BOX,
        "GRID": GRID,
        "WAVELENGTH": WAVELENGTH,
        "AMPLITUDE": AMPLITUDE,
        "REPS_por_condicao": REPS,
        "SEED_MASTER": SEED_MASTER,
        "alpha_nominal": ALPHA,
        "condicoes": ["nulo_A0", "sinal_X", "sinal_Y", "sinal_Z"],
        "total_catalogos": int(len(df)),
        "metrica": "potência FFT axial média dos modos conjugados no k-alvo",
        "janela": "Hann separável 3D",
        "teste_nulo_eixos": "Wilcoxon pareado dentro de cada catálogo",
        "teste_sinal_vs_nulo": "Mann–Whitney bilateral; grupos independentes",
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
    }
    (OUTPUT_DIR / "manifesto.json").write_text(
        json.dumps(manifesto, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("\n=== TESTE XYZ CONCLUÍDO ===")
    print(f"Catálogos: {len(df)}")
    print(f"Saída: {OUTPUT_DIR}")
    print("Atenção: os valores-p são exploratórios; ainda falta")
    print("corrigir multiplicidade e validar o nível de falso positivo.")


if __name__ == "__main__":
    rodar_experimento()
