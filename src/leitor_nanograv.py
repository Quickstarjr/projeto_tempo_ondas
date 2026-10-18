"""
leitor_nanograv.py — Leitor de dados NANOGrav 15yr para o pipeline.

Autores: Quickstar + Gepeto + Grokinha + Gemini + Deep (DeepSeek)
Data: 16 de outubro de 2026

Este módulo lê os dados do NANOGrav 15yr (release v2.1.0) e os
converte para o formato aceito pelo pipeline_v2.py.

FORMATO DE ENTRADA:
  - .par (narrowband/par/): ELONG/ELAT em radianos (eclíptica)
  - .avg.res (residuals/): tabela ASCII com header # (3 linhas)
    * Pulsares SEM red noise: 4 colunas
        avg_MJD | avg_freq(MHz) | avg_residual(us) | avg_uncertainty(us)
    * Pulsares COM red noise: 5 colunas
        avg_MJD | avg_freq(MHz) | avg_residual(us) | avg_white_residual(us) | avg_uncertainty(us)

FORMATO DE SAÍDA:
  DataFrame com colunas: pulsar_id | ra_deg | dec_deg | mjd | residual_us | erro_us
  (exatamente o que pipeline_v2.py espera)
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd


# Obliquidade da eclíptica em J2000 (radianos)
EPSILON_J2000 = np.radians(23.439291111)


# ============================================================
# CONVERSÃO ECLÍPTICA → EQUATORIAL
# ============================================================

def ecliptic_to_equatorial(elong_rad, elat_rad, epsilon=EPSILON_J2000):
    """
    Converte coordenadas eclípticas (λ, β) para equatoriais (α, δ).

    λ = ELONG (radianos), β = ELAT (radianos)
    Retorna (ra_rad, dec_rad) no intervalo [0, 2π) e [-π/2, π/2].
    """
    sin_dec = (np.sin(elat_rad) * np.cos(epsilon)
               + np.cos(elat_rad) * np.sin(epsilon) * np.sin(elong_rad))
    dec_rad = np.arcsin(np.clip(sin_dec, -1.0, 1.0))

    y = (-np.sin(elat_rad) * np.sin(epsilon)
         + np.cos(elat_rad) * np.cos(epsilon) * np.sin(elong_rad))
    x = np.cos(elat_rad) * np.cos(elong_rad)
    ra_rad = np.arctan2(y, x) % (2 * np.pi)

    return ra_rad, dec_rad


# ============================================================
# LEITURA DO .par
# ============================================================

def ler_par(caminho_par):
    """
    Lê um arquivo .par e extrai PSR, ELONG, ELAT.
    Também aceita RAJ/DECJ como fallback (alguns .par usam equatorial).

    Retorna dict: pulsar_id, ra_deg, dec_deg, elong_rad, elat_rad
    """
    dados = {}
    caminho_par = Path(caminho_par)

    with open(caminho_par, 'r', encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith('#'):
                continue
            partes = linha.split()
            if len(partes) < 2:
                continue
            chave = partes[0].upper()

            if chave in ('PSR', 'PSRJ'):
                dados['pulsar_id'] = partes[1]
            elif chave == 'ELONG':
               dados['elong_deg'] = float(partes[1]) 
            elif chave == 'ELAT':
                dados['elat_deg'] = float(partes[1])
            elif chave == 'RAJ':
                dados['raj'] = partes[1]
            elif chave == 'DECJ':
                dados['decj'] = partes[1]

    if 'pulsar_id' not in dados:
        raise ValueError(f"PSR/PSRJ não encontrado em {caminho_par}")

     # Preferir ELONG/ELAT (padrão do NANOGrav, em GRAUS)
    if 'elong_deg' in dados and 'elat_deg' in dados:
        elong_rad = np.radians(dados['elong_deg'])
        elat_rad = np.radians(dados['elat_deg'])
        ra_rad, dec_rad = ecliptic_to_equatorial(elong_rad, elat_rad)
    elif 'raj' in dados and 'decj' in dados:
        ra_rad = _hms_to_rad(dados['raj'])
        dec_rad = _dms_to_rad(dados['decj'])
    else:
        raise ValueError(f"Sem coordenadas em {caminho_par}")

    dados['ra_deg'] = float(np.degrees(ra_rad))
    dados['dec_deg'] = float(np.degrees(dec_rad))
    return dados


def _hms_to_rad(hms):
    """Converte 'HH:MM:SS.SSS' → radianos."""
    h, m, s = hms.split(':')
    hours = float(h) + float(m) / 60 + float(s) / 3600
    return np.radians(hours * 15)


def _dms_to_rad(dms):
    """Converte 'DD:MM:SS.SSS' (com sinal) → radianos."""
    sinal = -1 if dms.strip().startswith('-') else 1
    dms = dms.lstrip('+-')
    d, m, s = dms.split(':')
    deg = sinal * (float(d) + float(m) / 60 + float(s) / 3600)
    return np.radians(deg)


# ============================================================
# LEITURA DO .avg.res
# ============================================================

def ler_residuals(caminho_res, coluna='residual'):
    """
    Lê um arquivo .avg.res e retorna DataFrame com mjd, freq_mhz,
    residual_us e erro_us.

    coluna: 'residual' (un-whitened, padrão) ou 'white_residual' (whitened).
    Detecta automaticamente se o arquivo tem 4 ou 5 colunas.
    """
    caminho_res = Path(caminho_res)

    data = np.loadtxt(caminho_res, comments='#')
    if data.ndim == 1:
        data = data.reshape(1, -1)

    n_cols = data.shape[1]

    if n_cols == 4:
        # Sem red noise
        df = pd.DataFrame({
            'mjd': data[:, 0],
            'freq_mhz': data[:, 1],
            'residual_us': data[:, 2],
            'erro_us': data[:, 3],
        })
    elif n_cols == 5:
        # Com red noise — coluna 2 = un-whitened, coluna 3 = whitened
        idx = 3 if coluna == 'white_residual' else 2
        df = pd.DataFrame({
            'mjd': data[:, 0],
            'freq_mhz': data[:, 1],
            'residual_us': data[:, idx],
            'erro_us': data[:, 4],
        })
    else:
        raise ValueError(
            f"Número inesperado de colunas ({n_cols}) em {caminho_res}"
        )

    return df


# ============================================================
# PAREAMENTO .res ↔ .par
# ============================================================

def extrair_pulsar_id_do_res(caminho_res):
    """
    Extrai 'J0030+0451' de 'J0030+0451_NG15yr_nb.avg.res'.
    """
    nome = Path(caminho_res).name
    return nome.split('_')[0]


def encontrar_par(pulsar_id, pasta_par):
    """
    Encontra o .par 'combinado' para um dado pulsar_id.
    Prefere arquivos SEM sufixo de backend (ao, gbt, etc.).
    """
    pasta_par = Path(pasta_par)
    candidatos = list(pasta_par.glob(f"{pulsar_id}*_PINT_*.nb.par"))
    if not candidatos:
        candidatos = list(pasta_par.glob(f"{pulsar_id}*.par"))

    if not candidatos:
        return None

    # Padrão para sufixo de backend logo após o pulsar_id
    # Ex: J1713+0747ao_PINT_...  (sufixo 'ao')
    #     J1713+0747_PINT_...    (sem sufixo — combinado)
    padrao_backend = re.compile(rf"^{re.escape(pulsar_id)}[a-z]+_")

    combinados = [c for c in candidatos if not padrao_backend.match(c.name)]
    if combinados:
        return sorted(combinados)[0]
    return sorted(candidatos)[0]


# ============================================================
# CARREGAMENTO COMPLETO
# ============================================================

def carregar_dataset_completo(
    pasta_residuals,
    pasta_par,
    coluna='residual',
    sample=None,
    debug=False,
):
    """
    Percorre todos os .avg.res, pareia com .par, e monta DataFrame final.

    sample: se int, processa apenas N pulsares (para teste rápido).
    debug:  se True, imprime informações por pulsar.
    """
    pasta_residuals = Path(pasta_residuals)
    pasta_par = Path(pasta_par)

    arquivos_res = sorted(pasta_residuals.glob("*_nb.avg.res"))

    if not arquivos_res:
        raise FileNotFoundError(
            f"Nenhum .avg.res encontrado em {pasta_residuals}"
        )

    if sample:
        arquivos_res = arquivos_res[:sample]

    if debug:
        print(f"[DEBUG] Encontrados {len(arquivos_res)} arquivos .avg.res")
        print(f"[DEBUG] Pasta de .par: {pasta_par}")

    todos = []
    falhas = []

    for caminho_res in arquivos_res:
        pulsar_id = extrair_pulsar_id_do_res(caminho_res)
        caminho_par = encontrar_par(pulsar_id, pasta_par)

        if caminho_par is None:
            falhas.append((pulsar_id, "sem .par"))
            continue

        try:
            par = ler_par(caminho_par)
            res = ler_residuals(caminho_res, coluna=coluna)
        except Exception as e:
            falhas.append((pulsar_id, str(e)))
            continue

        df = res.copy()
        df['pulsar_id'] = pulsar_id
        df['ra_deg'] = par['ra_deg']
        df['dec_deg'] = par['dec_deg']

        # Reordenar para o formato do pipeline
        df = df[['pulsar_id', 'ra_deg', 'dec_deg', 'mjd',
                 'residual_us', 'erro_us']]

        todos.append(df)

        if debug:
            print(f"  [+] {pulsar_id:15s}  "
                  f"RA={par['ra_deg']:7.3f}  DEC={par['dec_deg']:+7.3f}  "
                  f"n_toas={len(res):5d}  colunas={res.shape[1]}")

    if falhas:
        print(f"\n[AVISO] {len(falhas)} pulsares com problema:")
        for pid, motivo in falhas:
            print(f"  - {pid}: {motivo}")

    if not todos:
        raise RuntimeError("Nenhum pulsar carregado com sucesso.")

    df_final = pd.concat(todos, ignore_index=True)
    print(f"\n[+] Dataset final: {len(df_final)} observações de "
          f"{df_final['pulsar_id'].nunique()} pulsares.")
    return df_final


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Leitor NANOGrav 15yr → pipeline_v2'
    )
    parser.add_argument(
        '--residuals', required=True,
        help='Pasta com arquivos *.avg.res'
    )
    parser.add_argument(
        '--par', required=True,
        help='Pasta com arquivos *.nb.par'
    )
    parser.add_argument(
        '--output', default='data/synthetic/nanograv_real.csv',
        help='CSV de saída'
    )
    parser.add_argument(
        '--coluna', choices=['residual', 'white_residual'],
        default='residual', help='Qual coluna usar (padrão: residual)'
    )
    parser.add_argument(
        '--sample', type=int, default=None,
        help='Processar apenas N pulsares (para teste)'
    )
    parser.add_argument(
        '--debug', action='store_true',
        help='Imprime detalhes por pulsar'
    )
    args = parser.parse_args()

    print("=== LEITOR NANOGrav 15yr ===")
    print(f"Residuals: {args.residuals}")
    print(f"par:       {args.par}")
    print(f"Coluna:    {args.coluna}")
    print()

    df = carregar_dataset_completo(
        pasta_residuals=args.residuals,
        pasta_par=args.par,
        coluna=args.coluna,
        sample=args.sample,
        debug=args.debug,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[+] CSV salvo em: {output_path}")
    print()
    print(df.head())


if __name__ == '__main__':
    main()