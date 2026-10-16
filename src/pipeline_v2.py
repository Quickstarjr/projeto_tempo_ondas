"""
Pipeline PTA v2 — Investigação Tempo/Ondas/Observador
Autores: Quickstar + Gepeto + Grokinha + Gemini + Deep (DeepSeek)
Data: 16 de outubro de 2026

MUDANÇAS EM RELAÇÃO AO v1:
  1. Adiciona curva de Hellings-Downs (hd_curva) para comparação.
  2. Adiciona teste de recuperação com anisotropia direcional injetada.
  3. Adiciona binning de correlação por separação angular.
  4. Adiciona plots de diagnóstico (histograma, correlação vs theta, HD).
  5. Adiciona teste de sanidade com amplitude ajustável de sinal.

USO:
  python pipeline_v2.py --modo sanidade
  python pipeline_v2.py --modo anisotropia
  python pipeline_v2.py --modo diagnostico
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from pathlib import Path


# ============================================================
# 1. CURVA DE HELLINGS-DOWNS
# ============================================================

def hd_curva(theta_rad):
    """
    Curva de Hellings-Downs: correlação esperada entre resíduos
    de dois pulsares separados por ângulo theta (em radianos),
    para um fundo isotrópico de ondas gravitacionais.

    Referência: Hellings & Downs (1983), ApJ 265, L39.
    """
    x = (1.0 - np.cos(theta_rad)) / 2.0
    # Evitar log(0)
    x = np.clip(x, 1e-12, None)
    return 0.5 * x * np.log(x) - x / 6.0 + 1.0 / 3.0


# ============================================================
# 2. GERADOR DE DADOS SINTÉTICOS
# ============================================================

def gerar_dados_sinteticos_pta(
    n_pulsares=30,
    n_observacoes=120,
    amplitude_sinal=0.2,
    modo_anisotropia=None,
    seed=42,
):
    """
    Gera resíduos de tempo sintéticos para PTAs.

    Parâmetros:
      amplitude_sinal : float
          Amplitude da oscilação temporal injetada.
      modo_anisotropia : None | 'dipolar' | 'quadrupolar'
          None       → sinal idêntico para todos os pulsares (coerência global)
          'dipolar'  → modulação por cos(RA)
          'quadrupolar' → modulação por cos(2*RA)
      seed : int
          Semente aleatória para reprodutibilidade.

    Retorna: DataFrame com colunas
      pulsar_id, ra_deg, dec_deg, mjd, residual_us, erro_us
    """
    rng = np.random.default_rng(seed)

    ra = rng.uniform(0, 360, n_pulsares)
    dec = rng.uniform(-90, 90, n_pulsares)
    mjd = np.linspace(53000, 59000, n_observacoes)

    dados = []
    for i in range(n_pulsares):
        # Ruído branco
        ruido = rng.normal(0, 0.5, n_observacoes)

        # Sinal temporal base (comum a todos)
        sinal_base = amplitude_sinal * np.sin(2 * np.pi * mjd / 365.25 / 10)

        # Modulação direcional (se pedida)
        if modo_anisotropia == 'dipolar':
            modulacao = np.cos(np.radians(ra[i]))
        elif modo_anisotropia == 'quadrupolar':
            modulacao = np.cos(2 * np.radians(ra[i]))
        elif modo_anisotropia is None:
            modulacao = 1.0
        else:
            raise ValueError(f"modo_anisotropia inválido: {modo_anisotropia}")

        residuos = ruido + sinal_base * modulacao

        for t_idx, t in enumerate(mjd):
            dados.append({
                'pulsar_id': f'J{i:02d}',
                'ra_deg': ra[i],
                'dec_deg': dec[i],
                'mjd': t,
                'residual_us': residuos[t_idx],
                'erro_us': rng.uniform(0.05, 0.15),
            })

    return pd.DataFrame(dados)


# ============================================================
# 3. SEPARAÇÃO ANGULAR
# ============================================================

def calcular_separacao_angular(ra1, dec1, ra2, dec2):
    """Separação angular (radianos) via produto escalar."""
    ra1_rad, dec1_rad = np.radians(ra1), np.radians(dec1)
    ra2_rad, dec2_rad = np.radians(ra2), np.radians(dec2)

    cos_theta = (
        np.sin(dec1_rad) * np.sin(dec2_rad)
        + np.cos(dec1_rad) * np.cos(dec2_rad) * np.cos(ra1_rad - ra2_rad)
    )
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    return np.arccos(cos_theta)


# ============================================================
# 4. MATRIZ DE CORRELAÇÃO POR PARES
# ============================================================

def extrair_matriz_correlacao_espacial(df_pta):
    """
    Calcula correlação de Pearson entre resíduos de cada par de pulsares
    ao longo do tempo, associando à separação angular.
    """
    pivot_df = df_pta.pivot(index='mjd', columns='pulsar_id', values='residual_us')
    matriz_corr = pivot_df.corr()

    coords = (
        df_pta[['pulsar_id', 'ra_deg', 'dec_deg']]
        .drop_duplicates()
        .set_index('pulsar_id')
    )

    pulsares = matriz_corr.columns.tolist()
    n = len(pulsares)

    pares = []
    for i in range(n):
        for j in range(i + 1, n):
            p1, p2 = pulsares[i], pulsares[j]
            ra1, dec1 = coords.loc[p1, 'ra_deg'], coords.loc[p1, 'dec_deg']
            ra2, dec2 = coords.loc[p2, 'ra_deg'], coords.loc[p2, 'dec_deg']
            theta_rad = calcular_separacao_angular(ra1, dec1, ra2, dec2)
            corr_val = matriz_corr.loc[p1, p2]

            pares.append({
                'pulsar_1': p1,
                'pulsar_2': p2,
                'theta_deg': np.degrees(theta_rad),
                'theta_rad': theta_rad,
                'correlacao_residuos': corr_val,
                'hd_esperado': hd_curva(theta_rad),
            })

    return pd.DataFrame(pares)


# ============================================================
# 5. BINNING POR SEPARAÇÃO ANGULAR
# ============================================================

def binnar_por_theta(df_pares, n_bins=10):
    """
    Agrupa correlações em bins de separação angular e retorna
    média, erro padrão e contagem por bin.
    """
    df = df_pares.copy()
    df['bin'] = pd.cut(df['theta_deg'], bins=n_bins)

    resumo = df.groupby('bin', observed=True).agg(
        theta_medio=('theta_deg', 'mean'),
        theta_rad_medio=('theta_rad', 'mean'),
        corr_media=('correlacao_residuos', 'mean'),
        corr_erro=('correlacao_residuos', 'sem'),
        hd_medio=('hd_esperado', 'mean'),
        n_pares=('correlacao_residuos', 'count'),
    ).reset_index(drop=True)

    return resumo


# ============================================================
# 6. PLOTS DE DIAGNÓSTICO
# ============================================================

def plotar_diagnosticos(df_pares, df_bins, titulo, arquivo_saida):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # (a) Histograma das correlações
    ax = axes[0]
    ax.hist(df_pares['correlacao_residuos'], bins=30, alpha=0.7, edgecolor='black')
    ax.axvline(0, color='red', linestyle='--', label='zero')
    ax.axvline(df_pares['correlacao_residuos'].mean(), color='green',
               linestyle='-', label=f"média={df_pares['correlacao_residuos'].mean():.3f}")
    ax.set_xlabel('Correlação de Pearson')
    ax.set_ylabel('Contagem')
    ax.set_title(f'{titulo} — Distribuição das correlações')
    ax.legend()

    # (b) Correlação vs theta + HD
    ax = axes[1]
    ax.scatter(df_pares['theta_deg'], df_pares['correlacao_residuos'],
               alpha=0.3, s=10, label='pares')
    ax.errorbar(df_bins['theta_medio'], df_bins['corr_media'],
                yerr=df_bins['corr_erro'], fmt='o', color='red',
                capsize=3, label='média por bin')
    ax.plot(df_bins['theta_medio'], df_bins['hd_medio'],
            'g--', label='Hellings-Downs')
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Separação angular (graus)')
    ax.set_ylabel('Correlação')
    ax.set_title(f'{titulo} — Correlação vs θ')
    ax.legend()

    # (c) Resíduo em relação a HD
    ax = axes[2]
    residuo = df_bins['corr_media'] - df_bins['hd_medio']
    ax.errorbar(df_bins['theta_medio'], residuo,
                yerr=df_bins['corr_erro'], fmt='o', color='purple', capsize=3)
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Separação angular (graus)')
    ax.set_ylabel('corr_media − HD')
    ax.set_title(f'{titulo} — Desvio em relação a HD')

    plt.tight_layout()
    plt.savefig(str(arquivo_saida), dpi=120)
    plt.close()
    print(f"[+] Plot salvo em: {arquivo_saida}")


# ============================================================
# 7. MODOS DE EXECUÇÃO
# ============================================================

def modo_sanidade(output_dir):
    """Teste de sanidade: sinal forte, sem anisotropia. Deve recuperar correlação alta."""
    print("=== MODO SANIDADE ===")
    print("Sinal: amplitude 2.0, sem anisotropia. Esperado: correlação alta entre todos os pares.")
    df = gerar_dados_sinteticos_pta(
        n_pulsares=30, n_observacoes=200,
        amplitude_sinal=2.0, modo_anisotropia=None, seed=1,
    )
    df.to_csv(output_dir / 'sanidade_residuos.csv', index=False)
    pares = extrair_matriz_correlacao_espacial(df)
    pares.to_csv(output_dir / 'sanidade_pares.csv', index=False)

    print(f"Média das correlações: {pares['correlacao_residuos'].mean():.3f}")
    print(f"Desvio padrão: {pares['correlacao_residuos'].std():.3f}")
    print("Se a média for > 0.7, o pipeline está recuperando o sinal coerente corretamente.")


def modo_anisotropia(output_dir):
    """Teste de recuperação: injeta anisotropia dipolar e verifica se aparece em θ."""
    print("=== MODO ANISOTROPIA (dipolar) ===")
    print("Sinal: amplitude 1.0, modulação cos(RA). Esperado: dependência em θ.")
    df = gerar_dados_sinteticos_pta(
        n_pulsares=30, n_observacoes=200,
        amplitude_sinal=1.0, modo_anisotropia='dipolar', seed=2,
    )
    pares = extrair_matriz_correlacao_espacial(df)
    bins = binnar_por_theta(pares, n_bins=10)

    print(bins[['theta_medio', 'corr_media', 'corr_erro', 'n_pares']])
    plotar_diagnosticos(pares, bins, 'Anisotropia dipolar',
                        output_dir / 'anisotropia_dipolar.png')

    pares.to_csv(output_dir / 'anisotropia_pares.csv', index=False)
    bins.to_csv(output_dir / 'anisotropia_bins.csv', index=False)


def modo_diagnostico(output_dir):
    """Modo padrão: ruído branco + sinal fraco idêntico. Esperado: correlações próximas de zero."""
    print("=== MODO DIAGNÓSTICO (sinal fraco) ===")
    df = gerar_dados_sinteticos_pta(
        n_pulsares=30, n_observacoes=120,
        amplitude_sinal=0.0, modo_anisotropia=None, seed=42,
    )
    df.to_csv(output_dir / 'diagnostico_residuos.csv', index=False)

    pares = extrair_matriz_correlacao_espacial(df)
    pares.to_csv(output_dir / 'diagnostico_pares.csv', index=False)

    bins = binnar_por_theta(pares, n_bins=10)
    bins.to_csv(output_dir / 'diagnostico_bins.csv', index=False)

    print(f"Nº de pares: {len(pares)}")
    print(f"Média das correlações: {pares['correlacao_residuos'].mean():.4f}")
    print(f"Desvio padrão: {pares['correlacao_residuos'].std():.4f}")
    print(f"Esperado (ruído branco, N=120): sigma ≈ {1/np.sqrt(120):.4f}")
    print(bins[['theta_medio', 'corr_media', 'corr_erro', 'n_pares']])

    plotar_diagnosticos(pares, bins, 'Diagnóstico sinal fraco',
                        output_dir / 'diagnostico.png')


# ============================================================
# 8. MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Pipeline PTA v2')
    parser.add_argument('--modo', choices=['sanidade', 'anisotropia', 'diagnostico'],
                        default='diagnostico', help='Modo de execução')
    parser.add_argument('--output', default='.', help='Diretório de saída')
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    print("=== PIPELINE PTA v2 — INVESTIGAÇÃO TEMPO/ONDAS/OBSERVADOR ===\n")

    if args.modo == 'sanidade':
        modo_sanidade(output_dir)
    elif args.modo == 'anisotropia':
        modo_anisotropia(output_dir)
    elif args.modo == 'diagnostico':
        modo_diagnostico(output_dir)

    print("\nPipeline concluído.")


if __name__ == '__main__':
    main()