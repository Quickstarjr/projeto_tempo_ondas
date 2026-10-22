#!/usr/bin/env python3
"""
Auditoria independente da construção de grades 3D.

Compara:
  A) Caixa cúbica centrada no ponto médio dos limites dos dados.
  B) Caixa cúbica centrada na origem do observador (0, 0, 0).

Não modifica os CSVs nem importa os scripts originais.
Não executa KDE ou FFT nesta etapa.
"""

import numpy as np
import pandas as pd


ARQUIVO = "outputs/reports/galaxias_tamanho/dados.csv"
N_GRID = 96
MARGEM_RELATIVA = 1e-9


def carregar_coordenadas(caminho):
    df = pd.read_csv(caminho)

    colunas_obrigatorias = [
        "x_mpc", "y_mpc", "dist_mpc", "dec"
    ]
    faltantes = [c for c in colunas_obrigatorias if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas ausentes no CSV: {faltantes}")

    x = df["x_mpc"].to_numpy(dtype=float)
    y = df["y_mpc"].to_numpy(dtype=float)

    if "z_mpc" in df.columns:
        z = df["z_mpc"].to_numpy(dtype=float)
        fonte_z = "coluna z_mpc existente"
    else:
        z = (
            df["dist_mpc"].to_numpy(dtype=float)
            * np.sin(np.radians(df["dec"].to_numpy(dtype=float)))
        )
        fonte_z = "dist_mpc * sin(dec)"

    pontos_originais = np.column_stack((x, y, z))
    validos = np.isfinite(pontos_originais).all(axis=1)
    pontos = pontos_originais[validos]

    if len(pontos) == 0:
        raise ValueError("Nenhuma coordenada finita encontrada.")

    return df, pontos, validos, fonte_z


def diagnosticar_caixa(nome, pontos, centro, lado, n_grid):
    """
    A caixa é [centro-lado/2, centro+lado/2) em cada eixo.
    A margem é incluída no lado calculado antes da chamada.
    """
    metade = lado / 2.0
    inferior = centro - metade
    superior = centro + metade

    dentro = np.all(
        (pontos >= inferior) & (pontos < superior),
        axis=1
    )

    contagem = int(dentro.sum())
    excluidas = len(pontos) - contagem
    retencao = 100.0 * contagem / len(pontos)

    dx = lado / n_grid
    memoria_grade = n_grid**3 * np.dtype(np.float64).itemsize

    print("\n" + "=" * 76)
    print(nome)
    print("=" * 76)
    print(
        f"Centro (Mpc)       : "
        f"({centro[0]:.6f}, {centro[1]:.6f}, {centro[2]:.6f})"
    )
    print(f"Lado da caixa      : {lado:.6f} Mpc")
    print(
        f"Limite inferior    : "
        f"({inferior[0]:.6f}, {inferior[1]:.6f}, {inferior[2]:.6f})"
    )
    print(
        f"Limite superior    : "
        f"({superior[0]:.6f}, {superior[1]:.6f}, {superior[2]:.6f})"
    )
    print(f"Grade              : {n_grid} x {n_grid} x {n_grid}")
    print(f"Total de células   : {n_grid**3:,}")
    print(f"Espaçamento dx     : {dx:.6f} Mpc")
    print(f"Volume da caixa    : {lado**3:.3f} Mpc³")
    print(f"Células por Mpc³   : {1.0 / dx**3:.9f}")
    print(f"Memória de 1 grade : {memoria_grade / 1024**2:.2f} MiB")
    print(f"Galáxias incluídas : {contagem:,}")
    print(f"Galáxias excluídas : {excluidas:,}")
    print(f"Percentual retido  : {retencao:.3f}%")

    # A grade usa pontos periódicos sem duplicar o extremo superior.
    eixo = inferior[0] + np.arange(n_grid) * dx
    print(f"Primeiro ponto X   : {eixo[0]:.6f} Mpc")
    print(f"Último ponto X     : {eixo[-1]:.6f} Mpc")
    print(f"Extremo superior X : {superior[0]:.6f} Mpc (exclusivo)")

    return {
        "nome": nome,
        "lado": lado,
        "dx": dx,
        "incluidas": contagem,
        "excluidas": excluidas,
        "retencao_pct": retencao,
        "centro": centro,
    }


def main():
    print("=" * 76)
    print("AUDITORIA DA CONSTRUÇÃO DA GRADE — GEPETO")
    print("=" * 76)

    df, pontos, validos, fonte_z = carregar_coordenadas(ARQUIVO)

    minimo = pontos.min(axis=0)
    maximo = pontos.max(axis=0)
    amplitudes = maximo - minimo
    centro_limites = (minimo + maximo) / 2.0

    # Caixa A: tamanho mínimo cúbico para conter a extensão dos dados.
    lado_bounds_base = float(amplitudes.max())
    lado_bounds = lado_bounds_base * (1.0 + MARGEM_RELATIVA)

    # Caixa B: menor cubo centrado no observador que contém todos os pontos.
    # Usa o maior valor absoluto de qualquer coordenada.
    lado_observador_base = float(2.0 * np.max(np.abs(pontos)))
    lado_observador = lado_observador_base * (1.0 + MARGEM_RELATIVA)

    print(f"Arquivo               : {ARQUIVO}")
    print(f"Linhas no CSV         : {len(df):,}")
    print(f"Coordenadas válidas   : {len(pontos):,}")
    print(f"Linhas inválidas      : {len(df) - len(pontos):,}")
    print(f"Fonte da coordenada Z : {fonte_z}")
    print(f"Resolução solicitada  : {N_GRID}³")
    print("\n=== LIMITES DOS DADOS ===")

    nomes = ("X", "Y", "Z")
    for i, nome in enumerate(nomes):
        print(
            f"{nome}: min={minimo[i]:.6f}, max={maximo[i]:.6f}, "
            f"amplitude={amplitudes[i]:.6f} Mpc"
        )

    print(
        "\nCentro dos limites: "
        f"({centro_limites[0]:.6f}, "
        f"{centro_limites[1]:.6f}, "
        f"{centro_limites[2]:.6f}) Mpc"
    )
    print(f"Lado base caixa delimitadora : {lado_bounds_base:.6f} Mpc")
    print(f"Lado base caixa observador   : {lado_observador_base:.6f} Mpc")

    a = diagnosticar_caixa(
        "CAIXA A — CENTRO DOS LIMITES",
        pontos,
        centro_limites,
        lado_bounds,
        N_GRID,
    )

    b = diagnosticar_caixa(
        "CAIXA B — ORIGEM DO OBSERVADOR (0, 0, 0)",
        pontos,
        np.zeros(3),
        lado_observador,
        N_GRID,
    )

    print("\n" + "=" * 76)
    print("COMPARAÇÃO FINAL")
    print("=" * 76)
    print(f"{'Métrica':<26} {'Caixa A':>20} {'Caixa B':>20}")
    print("-" * 70)
    print(f"{'Lado (Mpc)':<26} {a['lado']:20.6f} {b['lado']:20.6f}")
    print(f"{'dx (Mpc)':<26} {a['dx']:20.6f} {b['dx']:20.6f}")
    print(f"{'Incluídas':<26} {a['incluidas']:20d} {b['incluidas']:20d}")
    print(f"{'Excluídas':<26} {a['excluidas']:20d} {b['excluidas']:20d}")
    print(
        f"{'Retenção (%)':<26} "
        f"{a['retencao_pct']:19.3f}% {b['retencao_pct']:19.3f}%"
    )

    print("\nINTERPRETAÇÃO")
    print("- As duas caixas foram dimensionadas para conter os dados.")
    print("- Como os lados podem diferir, a resolução física dx também pode diferir.")
    print("- Mesmo N não significa mesma resolução espacial.")
    print("- Esta etapa testa geometria e seleção, não detecta ondas cósmicas.")
    print("- Nenhum arquivo original foi alterado.")


if __name__ == "__main__":
    main()
