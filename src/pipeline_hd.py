"""
pipeline_hd.py — Teste de recuperação de Hellings-Downs.

Autores: Quickstar + Gepeto + Grokinha + Gemini + Deep (DeepSeek)
Data: 16 de outubro de 2026

OBJETIVO (Teste 2 do framework Gepeto):
  Injetar um sinal de HD CONHECIDO em dados sintéticos com ruído
  realista e verificar se o pipeline atual o recupera.

  Se recuperar -> pipeline está OK; sensibilidade é o gargalo em
                  dados reais (red noise).
  Se não recuperar -> pipeline tem problema estrutural que precisa
                      ser corrigido ANTES de testar H17/H18.

MÉTODO:
  1. Gerar N pulsares em posições aleatórias.
  2. Construir matriz de correlação HD C_ij = Γ(θ_ij).
  3. Amostrar sinal correlacionado via decomposição de Cholesky.
  4. Adicionar ruído branco por pulsar.
  5. (Opcional) Adicionar ruído vermelho por pulsar.
  6. Rodar o pipeline e comparar Γ_recuperado(θ) com HD(θ).
  7. Varrer amplitude do sinal para achar limiar de detecção.

USO:
  py src/pipeline_hd.py --n-pulsares 30 --amplitude 1.0
  py src/pipeline_hd.py --scan
  py src/pipeline_hd.py --scan --com-red-noise
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# ============================================================
# HELLINGS-DOWNS
# ============================================================

def hd_curva(theta_rad):
    x = (1.0 - np.cos(theta_rad)) / 2.0
    x = np.clip(x, 1e-12, None)
    return 0.5 * x * np.log(x) - x / 6.0 + 1.0 / 3.0


def separacao_angular(ra1, dec1, ra2, dec2):
    ra1, dec1 = np.radians(ra1), np.radians(dec1)
    ra2, dec2 = np.radians(ra2), np.radians(dec2)
    cos_theta = (np.sin(dec1) * np.sin(dec2)
                 + np.cos(dec1) * np.cos(dec2) * np.cos(ra1 - ra2))
    return np.arccos(np.clip(cos_theta, -1.0, 1.0))


# ============================================================
# GERADOR DE SINAL HD CORRELACIONADO
# ============================================================

def construir_matriz_hd(ra, dec):
    """Matriz de correlação HD entre N pulsares."""
    n = len(ra)
    C = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                C[i, j] = 1.0
            else:
                theta = separacao_angular(ra[i], dec[i], ra[j], dec[j])
                C[i, j] = hd_curva(theta)
    return C


def gerar_sinal_hd(ra, dec, n_bins, amplitude, seed=42):
    """
    Gera sinal HD correlacionado entre N pulsares ao longo de n_bins.

    Retorna array de forma (n_bins, n_pulsares).
    """
    n_pulsares = len(ra)
    rng = np.random.default_rng(seed)

    C = construir_matriz_hd(ra, dec)

    # Regularização numérica (garante positiva definida)
    C += 1e-10 * np.eye(n_pulsares)

    try:
        L = np.linalg.cholesky(C)
    except np.linalg.LinAlgError:
        # Fallback: eigendecomposition
        eigs, vecs = np.linalg.eigh(C)
        eigs = np.clip(eigs, 0, None)
        L = vecs @ np.diag(np.sqrt(eigs))

    z = rng.standard_normal((n_bins, n_pulsares))
    sinal = (L @ z.T).T * amplitude
    return sinal


def gerar_ruido_vermelho(n_bins, amplitude_ruido, alpha=1.5, seed=42):
    """
    Gera ruído vermelho como ruído fracionário (simplificado).
    Aproximação: soma de senos com espectro em potência.
    """
    rng = np.random.default_rng(seed)
    freqs = np.fft.rfftfreq(n_bins, d=1.0)
    freqs[0] = freqs[1] if len(freqs) > 1 else 1.0

    # Amplitude espectral ~ f^(-alpha/2)
    amp = freqs ** (-alpha / 2.0)
    amp[0] = 0

    # Fases aleatórias
    fases = rng.uniform(0, 2 * np.pi, len(freqs))
    espectro = amp * np.exp(1j * fases)

    ruido = np.fft.irfft(espectro, n=n_bins)
    ruido = ruido / np.std(ruido) * amplitude_ruido
    return ruido


# ============================================================
# DATASET SINTÉTICO COMPLETO
# ============================================================

def gerar_dataset_hd(
    n_pulsares=30,
    n_bins=120,
    amplitude_sinal=1.0,
    amplitude_ruido_branco=1.0,
    amplitude_ruido_vermelho=0.0,
    seed=42,
):
    """
    Gera dataset sintético com sinal HD + ruído por pulsar.
    """
    rng = np.random.default_rng(seed)

    ra = rng.uniform(0, 360, n_pulsares)
    dec = np.degrees(np.arcsin(rng.uniform(-1, 1, n_pulsares)))

    sinal = gerar_sinal_hd(ra, dec, n_bins, amplitude_sinal, seed=seed)

    dados = []
    for i in range(n_pulsares):
        ruido_branco = rng.normal(0, amplitude_ruido_branco, n_bins)

        if amplitude_ruido_vermelho > 0:
            rn = gerar_ruido_vermelho(
                n_bins, amplitude_ruido_vermelho, seed=seed + i
            )
        else:
            rn = np.zeros(n_bins)

        residuos = sinal[:, i] + ruido_branco + rn

        for t_idx in range(n_bins):
            dados.append({
                'pulsar_id': f'P{i:02d}',
                'ra_deg': ra[i],
                'dec_deg': dec[i],
                'mjd': 53000 + t_idx * 30,
                'residual_us': residuos[t_idx],
                'erro_us': amplitude_ruido_branco,
            })

    return pd.DataFrame(dados), ra, dec


# ============================================================
# PIPELINE (reamostragem + correlação por par)
# ============================================================

def reamostrar(df, bin_dias=30):
    df = df.copy()
    df['bin_mjd'] = (df['mjd'] // bin_dias) * bin_dias
    return df


def calcular_pares(df, min_overlap=10):
    pivot = df.pivot(index='bin_mjd', columns='pulsar_id',
                     values='residual_us')
    coords = df.groupby('pulsar_id')[['ra_deg', 'dec_deg']].first()
    pulsares = pivot.columns.tolist()
    n = len(pulsares)

    pares = []
    for i in range(n):
        for j in range(i + 1, n):
            p1, p2 = pulsares[i], pulsares[j]
            s1, s2 = pivot[p1], pivot[p2]
            mascara = s1.notna() & s2.notna()
            n_overlap = int(mascara.sum())

            if n_overlap < min_overlap:
                continue

            corr = float(np.corrcoef(s1[mascara], s2[mascara])[0, 1])
            theta_rad = separacao_angular(
                coords.loc[p1, 'ra_deg'], coords.loc[p1, 'dec_deg'],
                coords.loc[p2, 'ra_deg'], coords.loc[p2, 'dec_deg'],
            )

            pares.append({
                'theta_deg': np.degrees(theta_rad),
                'theta_rad': theta_rad,
                'correlacao': corr,
                'hd_esperado': hd_curva(theta_rad),
            })

    return pd.DataFrame(pares)


def binnar(df_pares, n_bins=10):
    df = df_pares.copy()
    df['bin'] = pd.cut(df['theta_deg'], bins=n_bins)
    return df.groupby('bin', observed=True).agg(
        theta_medio=('theta_deg', 'mean'),
        corr_media=('correlacao', 'mean'),
        corr_erro=('correlacao', 'sem'),
        hd_medio=('hd_esperado', 'mean'),
        n_pares=('correlacao', 'count'),
    ).reset_index(drop=True)


# ============================================================
# MODO 1 — TESTE ÚNICO
# ============================================================

def teste_unico(
    n_pulsares=30,
    n_bins=120,
    amplitude=1.0,
    ruido_branco=1.0,
    ruido_vermelho=0.0,
    output_dir='outputs/plots',
):
    print("=== TESTE 2 — RECUPERAÇÃO DE HD ===")
    print(f"Pulsares:           {n_pulsares}")
    print(f"Bins temporais:     {n_bins}")
    print(f"Amplitude HD:       {amplitude}")
    print(f"Ruído branco:       {ruido_branco}")
    print(f"Ruído vermelho:     {ruido_vermelho}")
    print()

    df, _, _ = gerar_dataset_hd(
        n_pulsares=n_pulsares,
        n_bins=n_bins,
        amplitude_sinal=amplitude,
        amplitude_ruido_branco=ruido_branco,
        amplitude_ruido_vermelho=ruido_vermelho,
    )

    df = reamostrar(df, bin_dias=30)
    pares = calcular_pares(df)
    bins = binnar(pares)

    print(bins.to_string(index=False))

    # Estatística: correlação entre Γ_recuperado e HD_esperado
    from scipy.stats import pearsonr
    if len(bins) >= 3:
        r, p = pearsonr(bins['corr_media'], bins['hd_medio'])
        print(f"\n[+] Correlação Γ_recuperado × HD: r = {r:.3f}, p = {p:.3f}")
        if r > 0.7 and p < 0.05:
            print("    → Pipeline RECUPERA HD. ✅")
        elif r > 0.3:
            print("    → Pipeline recupera parcialmente.")
        else:
            print("    → Pipeline NÃO recupera HD. ❌")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(pares['theta_deg'], pares['correlacao'],
               alpha=0.3, s=10, label='pares')
    ax.errorbar(bins['theta_medio'], bins['corr_media'],
                yerr=bins['corr_erro'], fmt='o', color='red',
                capsize=3, label='bins')
    ax.plot(bins['theta_medio'], bins['hd_medio'], 'g--',
            label='HD esperada')
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('θ (graus)')
    ax.set_ylabel('Correlação')
    ax.set_title(f'Teste 2 — Recuperação HD (amp={amplitude})')
    ax.legend()
    plt.tight_layout()

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out / 'teste_hd.png'), dpi=120)
    plt.close()
    print(f"[+] Plot: {out / 'teste_hd.png'}")


# ============================================================
# MODO 2 — SCAN DE AMPLITUDE
# ============================================================

def teste_scan(
    n_pulsares=30,
    n_bins=120,
    amplitudes=None,
    ruido_vermelho=0.0,
    n_seeds=5,
    output_dir='outputs/plots',
):
    """
    Varre amplitude do sinal HD e verifica em que ponto o pipeline
    começa a recuperá-lo. Roda N seeds por amplitude para medir
    robustez estatística do limiar de sensibilidade.

    Referência: Passo 1 do plano consolidado (Deep + Gemini + Gepeto).
    """
    if amplitudes is None:
        amplitudes = np.logspace(-1, 1, 9)  # 0.1 a 10

    print("=== TESTE 2 — SCAN DE AMPLITUDE (5 SEEDS POR PONTO) ===")
    print(f"Amplitudes testadas: {amplitudes}")
    print(f"Ruído vermelho:      {ruido_vermelho}")
    print(f"Seeds por amplitude: {n_seeds}")
    print()

    from scipy.stats import pearsonr

    resultados = []
    for i_amp, amp in enumerate(amplitudes):
        r_seeds = []
        p_seeds = []

        for s in range(n_seeds):
            seed_s = 42 + 1000 * i_amp + s * 7919
            df, _, _ = gerar_dataset_hd(
                n_pulsares=n_pulsares,
                n_bins=n_bins,
                amplitude_sinal=amp,
                amplitude_ruido_branco=1.0,
                amplitude_ruido_vermelho=ruido_vermelho,
                seed=seed_s,
            )
            df = reamostrar(df)
            pares = calcular_pares(df)
            bins = binnar(pares)

            if len(bins) < 3:
                r, p = 0.0, 1.0
            else:
                r, p = pearsonr(bins['corr_media'], bins['hd_medio'])

            r_seeds.append(r)
            p_seeds.append(p)

        r_medio = float(np.mean(r_seeds))
        r_std = float(np.std(r_seeds))
        r_min = float(np.min(r_seeds))
        r_max = float(np.max(r_seeds))
        p_mediano = float(np.median(p_seeds))

        n_recupera = sum(
            1 for r, p in zip(r_seeds, p_seeds) if r > 0.7 and p < 0.05
        )
        fracao = n_recupera / n_seeds

        snr = amp / 1.0
        resultados.append({
            'amplitude': amp,
            'snr': snr,
            'r_medio': r_medio,
            'r_std': r_std,
            'r_min': r_min,
            'r_max': r_max,
            'p_mediano': p_mediano,
            'fracao_recupera': fracao,
        })

        print(
            f"  amp={amp:.3f}  SNR={snr:.2f}  "
            f"r={r_medio:.3f}±{r_std:.3f}  "
            f"(min={r_min:.2f}, max={r_max:.2f})  "
            f"p_med={p_mediano:.3f}  "
            f"recupera={n_recupera}/{n_seeds}"
        )

    df_res = pd.DataFrame(resultados)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    df_res.to_csv(out / 'scan_hd_5seeds.csv', index=False)

    # Plot com barras de erro
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.errorbar(
        df_res['snr'], df_res['r_medio'], yerr=df_res['r_std'],
        fmt='o-', capsize=3,
        label=f'média ± desvio ({n_seeds} seeds)'
    )
    ax.fill_between(
        df_res['snr'], df_res['r_min'], df_res['r_max'],
        alpha=0.2, label=f'min-max ({n_seeds} seeds)'
    )
    ax.axhline(0.7, color='red', linestyle='--', label='limiar r=0.7')
    ax.set_xscale('log')
    ax.set_xlabel('SNR (amplitude / ruído branco)')
    ax.set_ylabel('Pearson r (Γ_recuperado × HD)')
    ax.set_title(
        f'Teste 2 — Limiar de sensibilidade '
        f'({n_seeds} seeds por amplitude)'
    )
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(str(out / 'scan_hd_5seeds.png'), dpi=120)
    plt.close()
    print(f"\n[+] Resultados: {out / 'scan_hd_5seeds.csv'}")
    print(f"[+] Plot:       {out / 'scan_hd_5seeds.png'}")

# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Teste 2 — recuperação de HD injetada'
    )
    parser.add_argument('--n-pulsares', type=int, default=30)
    parser.add_argument('--n-bins', type=int, default=120)
    parser.add_argument('--amplitude', type=float, default=1.0)
    parser.add_argument('--ruido-branco', type=float, default=1.0)
    parser.add_argument('--ruido-vermelho', type=float, default=0.0)
    parser.add_argument('--output', default='outputs/plots')
    parser.add_argument('--scan', action='store_true',
                        help='Rodar scan de amplitude')
    args = parser.parse_args()

    if args.scan:
        teste_scan(
            n_pulsares=args.n_pulsares,
            n_bins=args.n_bins,
            ruido_vermelho=args.ruido_vermelho,
            output_dir=args.output,
        )
    else:
        teste_unico(
            n_pulsares=args.n_pulsares,
            n_bins=args.n_bins,
            amplitude=args.amplitude,
            ruido_branco=args.ruido_branco,
            ruido_vermelho=args.ruido_vermelho,
            output_dir=args.output,
        )


if __name__ == '__main__':
    main()