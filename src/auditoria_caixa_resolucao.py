#!/usr/bin/env python3

from pathlib import Path
import numpy as np
import pandas as pd
from astropy.cosmology import FlatLambdaCDM

CSV = Path("data/raw/galaxias_massa_z006_z008_100k.csv")
OUT = Path("outputs/reports/auditoria_caixa_resolucao")
OUT.mkdir(parents=True, exist_ok=True)

LAMBDA_ALVO = 100.0  # Mpc
CAIXAS = [660.0, 680.0, 700.0]
GRADES = [48, 64, 80, 96]

print("=" * 76)
print("AUDITORIA COMPARATIVA — CAIXA, RESOLUÇÃO E MODOS FFT")
print("=" * 76)

df = pd.read_csv(CSV, skiprows=1)
cosmo = FlatLambdaCDM(H0=70, Om0=0.3)

d = cosmo.comoving_distance(df["z"].to_numpy()).value
ra = np.deg2rad(df["ra"].to_numpy())
dec = np.deg2rad(df["dec"].to_numpy())

# Coordenadas cartesianas sem deslocamento artificial.
xyz = np.column_stack([
    d * np.cos(dec) * np.cos(ra),
    d * np.cos(dec) * np.sin(ra),
    d * np.sin(dec),
])

mins = xyz.min(axis=0)
maxs = xyz.max(axis=0)
span = maxs - mins

print(f"\nCatálogo: {CSV}")
print(f"Galáxias: {len(df):,}")
print("\nExtensão cartesiana real (Mpc):")
for eixo, lo, hi, largura in zip("XYZ", mins, maxs, span):
    print(f"  {eixo}: {lo:9.3f} até {hi:9.3f}"
          f" | extensão = {largura:8.3f} Mpc")

print(f"\nComprimento de onda alvo: {LAMBDA_ALVO:.3f} Mpc")
print("\nNota: k = 2π/λ. A FFT periódica só oferece modos discretos.")

rows = []

# Centro geométrico do intervalo observado em cada eixo.
# O mesmo centro será usado em todas as caixas para permitir
# uma comparação justa entre seus tamanhos.
centro_dados = (mins + maxs) / 2
xyz_centrado = xyz - centro_dados

print("\nCentro geométrico do catálogo (Mpc):")
for eixo, valor in zip("XYZ", centro_dados):
    print(f"  {eixo}: {valor:.6f}")

print("\nAuditoria de contenção por eixo:")
for L in CAIXAS:
    coords = xyz_centrado + L / 2
    dentro_eixo = (coords >= 0) & (coords < L)
    dentro_todos = np.all(dentro_eixo, axis=1)

    n_inside = int(dentro_todos.sum())
    n_outside = len(df) - n_inside

    fora_eixos = (~dentro_eixo).sum(axis=0)
    print(
        f"  L={L:.0f} Mpc | "
        f"fora X={fora_eixos[0]} | "
        f"fora Y={fora_eixos[1]} | "
        f"fora Z={fora_eixos[2]} | "
        f"fora em qualquer eixo={n_outside}"
    )

    if L < float(span.max()):
        print(
            f"    AVISO: a extensão máxima "
            f"({span.max():.3f} Mpc) excede a caixa."
        )

    for N in GRADES:
        dx = L / N
        dk = 2 * np.pi / L
        k_target = 2 * np.pi / LAMBDA_ALVO

        # Frequências FFT: k = 2π*m/L; m é o modo inteiro.
        mode = int(np.rint(k_target / dk))
        k_mode = mode * dk
        lambda_eff = 2 * np.pi / k_mode if mode else np.inf
        nyquist = np.pi / dx

        rows.append({
            "box_Mpc": L,
            "grid_N": N,
            "cell_Mpc": dx,
            "n_total": len(df),
            "n_inside": n_inside,
            "n_outside": n_outside,
            "outside_pct": 100 * n_outside / len(df),
            "outside_x": int(fora_eixos[0]),
            "outside_y": int(fora_eixos[1]),
            "outside_z": int(fora_eixos[2]),
            "center_x_Mpc": centro_dados[0],
            "center_y_Mpc": centro_dados[1],
            "center_z_Mpc": centro_dados[2],
            "lambda_target_Mpc": LAMBDA_ALVO,
            "mode_nearest": mode,
            "k_target_rad_Mpc": k_target,
            "k_mode_rad_Mpc": k_mode,
            "lambda_effective_Mpc": lambda_eff,
            "nyquist_rad_Mpc": nyquist,
            "target_below_nyquist": k_target < nyquist,
        })

        print(
            f"\nL={L:6.1f} Mpc | grade={N:3d}³"
            f" | célula={dx:6.3f} Mpc"
        )
        print(
            f"  Dentro: {n_inside:6d}/{len(df)}"
            f" | fora: {n_outside:5d} ({100*n_outside/len(df):.3f}%)"
        )
        print(
            f"  Modo mais próximo: m={mode}"
            f" | λ efetivo={lambda_eff:.3f} Mpc"
        )
        print(
            f"  Nyquist: {nyquist:.5f} rad/Mpc"
            f" | alvo abaixo de Nyquist: {k_target < nyquist}"
        )

result = pd.DataFrame(rows)
path = OUT / "comparacao_caixa_resolucao.csv"
result.to_csv(path, index=False)

print("\n" + "=" * 76)
print("RESUMO POR CAIXA")
print("=" * 76)
print(
    result.drop_duplicates("box_Mpc")[
        ["box_Mpc", "n_inside", "n_outside", "outside_pct",
         "outside_x", "outside_y", "outside_z"]
    ].to_string(index=False)
)

print("\nRelatório salvo em:", path)
print("\nATENÇÃO:")
print("- Esta auditoria mede geometria e resolução, não detecta ondas.")
print("- A contagem 'dentro' usa a caixa centralizada em cada configuração.")
print("- Mudar L altera os modos discretos; compare λ efetivo, não só o rótulo.")
print("- Uma caixa maior não corrige a máscara angular nem a seleção do SDSS.")
