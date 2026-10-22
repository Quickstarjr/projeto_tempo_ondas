#!/usr/bin/env python3
"""
Auditoria isolada da grade e da FFT 3D.
Não altera nem importa os scripts originais do projeto.
"""

import numpy as np


def testar_onda(comprimento_onda=100.0, fase=0.0):
    L = 500.0
    N = 64

    # Grade periódica correta: não duplica o ponto final.
    dx = L / N
    x = np.arange(N) * dx

    k_esperado = 2.0 * np.pi / comprimento_onda
    campo_1d = np.sin(k_esperado * x + fase)

    # Onda repetida nos outros dois eixos.
    campo_3d = np.broadcast_to(
        campo_1d[:, None, None], (N, N, N)
    ).copy()

    # FFT 3D e frequências angulares em rad/Mpc.
    transformada = np.fft.fftn(campo_3d)
    potencia = np.abs(transformada) ** 2

    freq = 2.0 * np.pi * np.fft.fftfreq(N, d=dx)
    KX, KY, KZ = np.meshgrid(
        freq, freq, freq, indexing="ij"
    )
    K = np.sqrt(KX**2 + KY**2 + KZ**2)

    # Ignora o modo zero e encontra o modo de maior potência.
    potencia[0, 0, 0] = 0.0
    indice = np.unravel_index(np.argmax(potencia), potencia.shape)

    modo_x = int(np.rint(freq[indice[0]] * L / (2 * np.pi)))
    k_encontrado = abs(freq[indice[0]])
    lambda_encontrado = (
        2.0 * np.pi / k_encontrado
        if k_encontrado > 0 else np.inf
    )

    return {
        "L": L,
        "N": N,
        "dx": dx,
        "fase": fase,
        "k_esperado": k_esperado,
        "k_encontrado": k_encontrado,
        "lambda_esperado": comprimento_onda,
        "lambda_encontrado": lambda_encontrado,
        "modo_x": modo_x,
        "indice_pico": indice,
        "potencia": potencia,
        "K": K,
    }


def main():
    print("=" * 65)
    print("AUDITORIA DE GRADE E FFT 3D — GEPETO")
    print("=" * 65)

    a = testar_onda(fase=0.0)
    b = testar_onda(fase=0.73)

    print("\n[1] GRADE PERIÓDICA")
    print(f"Lado da caixa       : {a['L']:.1f} Mpc")
    print(f"Células por eixo    : {a['N']}")
    print(f"Espaçamento dx      : {a['dx']:.6f} Mpc")
    print(f"Último ponto        : {(a['N']-1)*a['dx']:.6f} Mpc")
    print(f"Ponto final duplicado? Não")

    print("\n[2] RECUPERAÇÃO DA ONDA")
    print(f"Comprimento esperado: {a['lambda_esperado']:.3f} Mpc")
    print(f"k esperado          : {a['k_esperado']:.6f} rad/Mpc")
    print(f"k recuperado        : {a['k_encontrado']:.6f} rad/Mpc")
    print(f"Comprimento obtido  : {a['lambda_encontrado']:.3f} Mpc")
    print(f"Modo FFT encontrado : {a['modo_x']}")
    print(f"Índice do pico      : {a['indice_pico']}")

    erro = abs(a["lambda_encontrado"] - a["lambda_esperado"])
    ok_onda = erro < 1e-9 and abs(a["modo_x"]) == 5

    print("\n[3] TESTE DE MUDANÇA DE FASE")
    print(f"Fase A              : {a['fase']:.2f} rad")
    print(f"Fase B              : {b['fase']:.2f} rad")
    print(f"k recuperado A      : {a['k_encontrado']:.6f} rad/Mpc")
    print(f"k recuperado B      : {b['k_encontrado']:.6f} rad/Mpc")
    mesma_escala = np.isclose(
        a["k_encontrado"], b["k_encontrado"], rtol=1e-10
    )
    print(f"Mesma escala após mudar a fase? {'SIM' if mesma_escala else 'NÃO'}")

    print("\n[4] RESULTADO")
    print("PASSOU: onda recuperada corretamente." if ok_onda else
          "FALHOU: investigar a calibração da FFT.")
    print("PASSOU: fase não alterou o módulo de k." if mesma_escala else
          "FALHOU: a mudança de fase alterou o pico.")

    if not (ok_onda and mesma_escala):
        raise SystemExit(1)

    print("\nAuditoria concluída. Nenhum arquivo original foi alterado.")


if __name__ == "__main__":
    main()
