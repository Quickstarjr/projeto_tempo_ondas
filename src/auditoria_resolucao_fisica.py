#!/usr/bin/env python3
"""
Auditoria da resolução física das grades A e B.

A: caixa centrada no ponto médio dos extremos dos dados.
B: caixa centrada na origem do sistema de coordenadas.

Compara:
1. Mesmo N por eixo.
2. Mesma resolução física, sem alocar arrays 3D.

Não modifica scripts ou dados existentes.
"""

from pathlib import Path
import math
import numpy as np
import pandas as pd

ARQUIVO = Path("outputs/reports/galaxias_tamanho/dados.csv")
N_FIXO = 96
MARGEM_RELATIVA = 1e-9
BYTES_POR_VALOR = 8  # float64


def memoria_formatada(n_bytes):
    mib = n_bytes / (1024 ** 2)
    gib = n_bytes / (1024 ** 3)
    return f"{mib:,.2f} MiB ({gib:.3f} GiB)"


def diagnostico_grade(nome, centro, lado, n):
    dx = lado / n
    celulas = n ** 3
    bytes_um_campo = celulas * BYTES_POR_VALOR

    print(f"\n--- {nome} ---")
    print(f"Centro (Mpc)       : {centro}")
    print(f"Lado da caixa     : {lado:.6f} Mpc")
    print(f"Células por eixo  : {n}")
    print(f"Total de células  : {celulas:,}")
    print(f"Resolução dx      : {dx:.6f} Mpc")
    print(f"Volume da caixa   : {lado**3:,.3f} Mpc³")
    print(f"Memória 1 campo   : {memoria_formatada(bytes_um_campo)}")
    print(f"Memória 4 campos  : {memoria_formatada(4 * bytes_um_campo)}")

    return dx


def main():
    if not ARQUIVO.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {ARQUIVO}\n"
            "Confira se você está na raiz do projeto."
        )

    df = pd.read_csv(ARQUIVO)

    colunas = {"x_mpc", "y_mpc"}
    faltantes = colunas - set(df.columns)
    if faltantes:
        raise ValueError(f"Colunas ausentes: {sorted(faltantes)}")

    # Reconstrói z somente se não existir uma coluna z_mpc.
    if "z_mpc" in df.columns:
        z = pd.to_numeric(df["z_mpc"], errors="coerce").to_numpy()
        origem_z = "coluna z_mpc existente"
    elif {"dist_mpc", "dec"}.issubset(df.columns):
        distancia = pd.to_numeric(
            df["dist_mpc"], errors="coerce"
        ).to_numpy()
        dec = pd.to_numeric(df["dec"], errors="coerce").to_numpy()

        # Os valores de dec do catálogo estão em graus.
        z = distancia * np.sin(np.deg2rad(dec))
        origem_z = "dist_mpc * sin(dec)"
    else:
        raise ValueError(
            "Não há z_mpc nem as colunas dist_mpc e dec."
        )

    x = pd.to_numeric(df["x_mpc"], errors="coerce").to_numpy()
    y = pd.to_numeric(df["y_mpc"], errors="coerce").to_numpy()

    xyz = np.column_stack((x, y, z))
    validos = np.isfinite(xyz).all(axis=1)
    xyz = xyz[validos]

    if len(xyz) == 0:
        raise ValueError("Nenhuma coordenada válida.")

    minimo = xyz.min(axis=0)
    maximo = xyz.max(axis=0)
    spans = maximo - minimo
    centro_a = (minimo + maximo) / 2.0

    # A: caixa baseada na extensão dos dados.
    lado_a_minimo = float(spans.max())
    lado_a = lado_a_minimo * (1.0 + MARGEM_RELATIVA)

    # B: caixa centrada na origem, contendo todas as coordenadas.
    lado_b_minimo = 2.0 * float(np.abs(xyz).max())
    lado_b = lado_b_minimo * (1.0 + MARGEM_RELATIVA)

    centro_b = np.zeros(3)

    print("=" * 68)
    print("AUDITORIA DE RESOLUÇÃO FÍSICA — GRADES A E B")
    print("=" * 68)
    print(f"Arquivo            : {ARQUIVO}")
    print(f"Linhas originais   : {len(df):,}")
    print(f"Coordenadas válidas: {len(xyz):,}")
    print(f"Coordenadas inválidas: {(~validos).sum():,}")
    print(f"Origem de z        : {origem_z}")

    nomes = ["X", "Y", "Z"]
    for i, nome in enumerate(nomes):
        print(
            f"{nome}: min={minimo[i]:.6f}, "
            f"max={maximo[i]:.6f}, "
            f"extensão={spans[i]:.6f} Mpc"
        )

    print("\n" + "=" * 68)
    print("CENÁRIO 1 — MESMO N POR EIXO")
    print("=" * 68)

    dx_a = diagnostico_grade(
        "A — caixa dos extremos", centro_a, lado_a, N_FIXO
    )
    dx_b = diagnostico_grade(
        "B — caixa centrada na origem", centro_b, lado_b, N_FIXO
    )

    print("\nComparação:")
    print(f"dx B / dx A       : {dx_b / dx_a:.4f}x")
    print(f"Volume B / A      : {(lado_b / lado_a) ** 3:.4f}x")

    print("\n" + "=" * 68)
    print("CENÁRIO 2 — MESMA RESOLUÇÃO FÍSICA")
    print("=" * 68)

    # Usa dx de A como alvo. Em B, escolhe N suficiente para cobrir
    # o lado necessário; o lado efetivo B passa a ser N_B * dx_alvo.
    dx_alvo = dx_a
    n_a_comum = N_FIXO
    n_b_comum = math.ceil(lado_b / dx_alvo)
    lado_a_comum = n_a_comum * dx_alvo
    lado_b_comum = n_b_comum * dx_alvo

    dx_a_comum = diagnostico_grade(
        "A — resolução de referência", centro_a,
        lado_a_comum, n_a_comum
    )
    dx_b_comum = diagnostico_grade(
        "B — resolução equivalente", centro_b,
        lado_b_comum, n_b_comum
    )

    print("\nVerificação:")
    print(f"dx alvo           : {dx_alvo:.9f} Mpc")
    print(f"Diferença dx A/B  : {abs(dx_a_comum - dx_b_comum):.12f} Mpc")
    print(f"Lado efetivo A    : {lado_a_comum:.6f} Mpc")
    print(f"Lado efetivo B    : {lado_b_comum:.6f} Mpc")
    print(f"N B necessário    : {n_b_comum}³")
    print(f"Razão células B/A : {(n_b_comum / n_a_comum) ** 3:.2f}x")

    print("\n" + "=" * 68)
    print("INTERPRETAÇÃO")
    print("=" * 68)
    print(
        "1. Mesmo N não significa mesma resolução física.\n"
        "2. Mesma resolução física exige muito mais células na caixa B.\n"
        "3. A memória acima estima campos float64; FFT/KDE pode usar\n"
        "   arrays temporários adicionais.\n"
        "4. Esta auditoria não aloca grades 3D nem mede espectros.\n"
        "5. Ela não determina qual caixa é fisicamente correta.\n"
        "6. Próximo controle: máscara/seleção, bordas e KDE."
    )


if __name__ == "__main__":
    main()
