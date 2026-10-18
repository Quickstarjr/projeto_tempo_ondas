"""
pipeline_real.py — Análise de resíduos NANOGrav 15yr reais.

Autores: Quickstar + Gepeto + Grokinha + Gemini + Deep (DeepSeek)
Data: 16 de outubro de 2026
Pré-registro congelado em: commit cb4558b

DIFERENÇA CRÍTICA EM RELAÇÃO AO pipeline_v2.py:
  - NÃO gera dados sintéticos. Lê dados reais do NANOGrav 15yr.
  - Os pulsares reais têm MJDs DIFERENTES entre si. Não dá para
    pivotar diretamente. Este script reamostra para uma grade
    temporal comum antes de calcular correlações.
  - Reporta TODOS os bins, não só os significativos.
  - Inclui sky scramble como teste nulo.

LIMITAÇÕES CONHECIDAS (documentadas explicitamente):
  1. Reamostragem mensal introduz correlação artificial entre
     observações do mesmo pulsar dentro do mesmo bin.
  2. Não modela ruído vermelho intrínseco de cada pulsar.
     Isso pode dominar a correlação em baixas frequências.
  3. Não usa o optimal statistic da literatura. É uma versão
     simplificada, honesta sobre suas limitações.
  4. Não corrige efeito Shklovskii nem aceleração galáctica.
  5. Não usa catálogo externo de cosmic web.

USO:
  py src/pipeline_real.py --input data/synthetic/nanograv_15yr.csv
  py src/pipeline_real.py --input data/synthetic/nanograv_15yr.csv --debug
  py src/pipeline_real.py --input data/synthetic/nanograv_15yr.csv --sky-scramble 100
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Não abre janela, só salva
import matplotlib.pyplot as plt


# ============================================================
# HELLINGS-DOWNS
# ============================================================

def hd_curva(theta_rad):
    """Curva de Hellings-Downs (isotrópico)."""
    x = (1.0 - np.cos(theta_rad)) / 2.0
    x = np.clip(x, 1e-12, None)
    return 0.5 * x * np.log(x) - x / 6.0 + 1.0 / 3.0


def separacao_angular(ra1, dec1, ra2, dec2):
    """Separação angular (radianos) via produto escalar."""
    ra1, dec1 = np.radians(ra1), np.radians(dec1)
    ra2, dec2 = np.radians(ra2), np.radians(dec2)
    cos_theta = (np.sin(dec1) * np.sin(dec2)
                 + np.cos(dec1) * np.cos(dec2) * np.cos(ra1 - ra2))
    return np.arccos(np.clip(cos_theta, -1.0, 1.0))


# ============================================================
# REAMOSTRAGEM PARA GRADE TEMPORAL COMUM
# ============================================================

def reamostrar_por_bin(df, bin_dias=30):
    """
    Reamostra resíduos de cada pulsar para bins temporais comuns.

    Retorna DataFrame no formato:
        pulsar_id | bin_mjd | residual_medio | n_obs
    """
    df = df.copy()
    df['bin_mjd'] = (df['mjd'] // bin_dias) * bin_dias

    agrupado = df.groupby(['pulsar_id', 'bin_mjd']).agg(
        residual_medio=('residual_us', 'mean'),
        n_obs=('residual_us', 'count'),
    ).reset_index()

    return agrupado


def extrair_matriz_correlacao_real(df_reamostrado, min_overlap=10):
    """
    Para cada par de pulsares, calcula correlação de Pearson nos
    bins TEMPORAIS QUE SE SOBREPÕEM entre os dois.

    min_overlap: número mínimo de bins em comum para aceitar o par.

    Retorna DataFrame: pulsar_1 | pulsar_2 | theta_deg | corr | n_overlap
    """
    # Pivot: index=bin_mjd, columns=pulsar_id, values=residual_medio
    pivot = df_reamostrado.pivot(
        index='bin_mjd', columns='pulsar_id', values='residual_medio'
    )

    pulsares = pivot.columns.tolist()
    n = len(pulsares)

    coords = df_reamostrado.groupby('pulsar_id').first()[
        ['residual_medio']
    ].index.tolist()

    # Precisamos de RA/DEC — vem do df original
    # Este DataFrame não tem RA/DEC, então precisamos passar separado.
    # Para simplificar, o chamador passa.
    return pivot, pulsares


# ============================================================
# PARES COM OVERLAP TEMPORAL
# ============================================================

def calcular_pares(df_reamostrado, df_original, min_overlap=10):
    """
    Para cada par de pulsares:
      - Encontra bins em comum
      - Calcula Pearson nos bins em comum
      - Associa separação angular
    """
    pivot = df_reamostrado.pivot(
        index='bin_mjd', columns='pulsar_id', values='residual_medio'
    )

    # Coordenadas (uma linha por pulsar)
    coords = df_original.groupby('pulsar_id')[
        ['ra_deg', 'dec_deg']
    ].first()

    pulsares = pivot.columns.tolist()
    n = len(pulsares)

    pares = []
    descartados = 0

    for i in range(n):
        for j in range(i + 1, n):
            p1, p2 = pulsares[i], pulsares[j]
            serie1 = pivot[p1]
            serie2 = pivot[p2]

            # Bins em que ambos têm dados
            mascara = serie1.notna() & serie2.notna()
            n_overlap = int(mascara.sum())

            if n_overlap < min_overlap:
                descartados += 1
                continue

            corr = float(np.corrcoef(
                serie1[mascara].values,
                serie2[mascara].values,
            )[0, 1])

            theta_rad = separacao_angular(
                coords.loc[p1, 'ra_deg'], coords.loc[p1, 'dec_deg'],
                coords.loc[p2, 'ra_deg'], coords.loc[p2, 'dec_deg'],
            )

            pares.append({
                'pulsar_1': p1,
                'pulsar_2': p2,
                'theta_rad': theta_rad,
                'theta_deg': float(np.degrees(theta_rad)),
                'correlacao': corr,
                'hd_esperado': hd_curva(theta_rad),
                'n_overlap': n_overlap,
            })

    df_pares = pd.DataFrame(pares)
    print(f"[+] Pares com overlap >= {min_overlap} bins: {len(df_pares)}")
    print(f"[+] Pares descartados por falta de overlap: {descartados}")
    return df_pares


# ============================================================
# BINNING POR θ
# ============================================================

def binnar_por_theta(df_pares, n_bins=10):
    df = df_pares.copy()
    df['bin'] = pd.cut(df['theta_deg'], bins=n_bins)

    resumo = df.groupby('bin', observed=True).agg(
        theta_medio=('theta_deg', 'mean'),
        theta_rad_medio=('theta_rad', 'mean'),
        corr_media=('correlacao', 'mean'),
        corr_erro=('correlacao', 'sem'),
        hd_medio=('hd_esperado', 'mean'),
        n_pares=('correlacao', 'count'),
        n_overlap_medio=('n_overlap', 'mean'),
    ).reset_index(drop=True)

    return resumo


# ============================================================
# SKY SCRAMBLE (teste nulo)
# ============================================================

def sky_scramble(df_pares, n_scrambles=100, seed=42):
    """
    Teste nulo: embaralha aleatoriamente as RA/DEC dos pulsares e
    recomputa a estatística. Repete n_scrambles vezes.

    Retorna array com a estatística χ² em cada scramble, para
    comparação com o valor observado.
    """
    rng = np.random.default_rng(seed)

    # Estatística observada
    chi2_obs = chi2_contra_hd(df_pares)

    chi2_scrambles = []
    thetas_obs = df_pares['theta_deg'].values
    corrs = df_pares['correlacao'].values

    for i in range(n_scrambles):
        # Embaralhar os θ (equivalente a embaralhar as posições)
        thetas_shuffled = rng.permutation(thetas_obs)
        theta_rad = np.radians(thetas_shuffled)
        hd_shuffled = hd_curva(theta_rad)

        # χ² simplificado (sem erro por bin, é só um diagnóstico)
        chi2 = float(np.sum((corrs - hd_shuffled) ** 2))
        chi2_scrambles.append(chi2)

    chi2_scrambles = np.array(chi2_scrambles)
    p_valor = float(np.mean(chi2_scrambles >= chi2_obs))

    return {
        'chi2_observado': chi2_obs,
        'chi2_scrambles': chi2_scrambles,
        'p_valor': p_valor,
    }


def chi2_contra_hd(df_pares):
    """χ² simples entre correlação observada e HD."""
    return float(np.sum(
        (df_pares['correlacao'].values - df_pares['hd_esperado'].values) ** 2
    ))


# ============================================================
# PLOT
# ============================================================

def plotar_resultado(df_pares, df_bins, titulo, arquivo_saida,
                     scramble_result=None):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # (a) Scatter bruto
    ax = axes[0]
    ax.scatter(df_pares['theta_deg'], df_pares['correlacao'],
               alpha=0.4, s=15, label='pares reais')
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Separação angular θ (graus)')
    ax.set_ylabel('Correlação de Pearson')
    ax.set_title(f'{titulo} — Pares individuais')
    ax.legend()

    # (b) Bins com erro padrão + HD
    ax = axes[1]
    ax.errorbar(df_bins['theta_medio'], df_bins['corr_media'],
                yerr=df_bins['corr_erro'], fmt='o', color='red',
                capsize=3, label='média por bin')
    ax.plot(df_bins['theta_medio'], df_bins['hd_medio'],
            'g--', label='Hellings-Downs')
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Separação angular θ (graus)')
    ax.set_ylabel('Correlação')
    ax.set_title(f'{titulo} — Binado (todos os bins reportados)')
    ax.legend()

    # (c) Desvio em relação a HD
    ax = axes[2]
    residuo = df_bins['corr_media'] - df_bins['hd_medio']
    ax.errorbar(df_bins['theta_medio'], residuo,
                yerr=df_bins['corr_erro'], fmt='o',
                color='purple', capsize=3)
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Separação angular θ (graus)')
    ax.set_ylabel('corr_media − HD')
    ax.set_title(f'{titulo} — Desvio em relação a HD')
    if scramble_result is not None:
        ax.text(0.02, 0.98,
                f"p-valor (sky scramble): {scramble_result['p_valor']:.3f}",
                transform=ax.transAxes, va='top',
                bbox=dict(boxstyle='round', facecolor='wheat'))

    plt.tight_layout()
    plt.savefig(str(arquivo_saida), dpi=120)
    plt.close()
    print(f"[+] Plot salvo em: {arquivo_saida}")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Pipeline em dados reais NANOGrav 15yr'
    )
    parser.add_argument(
        '--input', required=True,
        help='CSV do NANOGrav (gerado por leitor_nanograv.py)'
    )
    parser.add_argument(
        '--output-plots', default='outputs/plots',
        help='Pasta para salvar plots'
    )
    parser.add_argument(
        '--output-reports', default='outputs/reports',
        help='Pasta para salvar relatórios'
    )
    parser.add_argument(
        '--bin-dias', type=int, default=30,
        help='Tamanho do bin temporal em dias (padrão 30)'
    )
    parser.add_argument(
        '--min-overlap', type=int, default=10,
        help='Mínimo de bins em comum para aceitar par (padrão 10)'
    )
    parser.add_argument(
        '--n-bins-theta', type=int, default=10,
        help='Número de bins angulares (padrão 10)'
    )
    parser.add_argument(
        '--sky-scramble', type=int, default=0,
        help='Número de scrambles para teste nulo (0 = desativado)'
    )
    parser.add_argument(
        '--debug', action='store_true',
        help='Imprime detalhes'
    )
    args = parser.parse_args()

    print("=== PIPELINE REAL — NANOGrav 15yr ===")
    print(f"Input: {args.input}")
    print(f"Bin temporal: {args.bin_dias} dias")
    print(f"Min overlap: {args.min_overlap} bins")
    print()

    # 1. Carregar dados
    df = pd.read_csv(args.input)
    print(f"[+] Carregado: {len(df)} observações de "
          f"{df['pulsar_id'].nunique()} pulsares")

    # 2. Reamostrar
    df_reamostrado = reamostrar_por_bin(df, bin_dias=args.bin_dias)
    print(f"[+] Reamostrado: {len(df_reamostrado)} bins temporais")

    # 3. Calcular pares
    df_pares = calcular_pares(
        df_reamostrado, df, min_overlap=args.min_overlap
    )
    if len(df_pares) == 0:
        print("[ERRO] Nenhum par com overlap suficiente.")
        return

    # 4. Binnar por theta
    df_bins = binnar_por_theta(df_pares, n_bins=args.n_bins_theta)

    # 5. Relatório
    print("\n=== BINS POR SEPARAÇÃO ANGULAR ===")
    print("(reportando TODOS os bins, conforme pré-registro)")
    print(df_bins.to_string(index=False))

    print(f"\n[+] Correlação média global: "
          f"{df_pares['correlacao'].mean():.4f}")
    print(f"[+] Desvio padrão: {df_pares['correlacao'].std():.4f}")

    # 6. Sky scramble
    scramble_result = None
    if args.sky_scramble > 0:
        print(f"\n[+] Rodando sky scramble ({args.sky_scramble} iterações)...")
        scramble_result = sky_scramble(
            df_pares, n_scrambles=args.sky_scramble
        )
        print(f"    χ² observado: {scramble_result['chi2_observado']:.2f}")
        print(f"    p-valor: {scramble_result['p_valor']:.3f}")
        if scramble_result['p_valor'] < 0.05:
            print("    → Desvio significativo de HD (p < 0.05)")
        else:
            print("    → Consistente com HD (p >= 0.05)")

    # 7. Salvar resultados
    output_plots = Path(args.output_plots)
    output_reports = Path(args.output_reports)
    output_plots.mkdir(parents=True, exist_ok=True)
    output_reports.mkdir(parents=True, exist_ok=True)

    df_pares.to_csv(output_reports / 'real_pares.csv', index=False)
    df_bins.to_csv(output_reports / 'real_bins.csv', index=False)

    plotar_resultado(
        df_pares, df_bins,
        'NANOGrav 15yr — Resíduos reais',
        output_plots / 'real_resultado.png',
        scramble_result=scramble_result,
    )

    print("\n[+] CSVs salvos em:", output_reports)
    print("[+] Pipeline concluído.")


if __name__ == '__main__':
    main()