#!/usr/bin/env python3
"""Auditoria descritiva da seleção do catálogo, sem grade 3D."""

from pathlib import Path
import numpy as np
import pandas as pd

ARQUIVO = Path("outputs/reports/galaxias_tamanho/dados.csv")
SAIDA = Path("outputs/reports/galaxias_tamanho/auditoria_selecao_catalogo")

N_BINS_RA = 12
N_BINS_DEC = 6
N_BINS_DIST = 10
QUANTIS = [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100]


def resumo(nome, serie):
    valores = pd.to_numeric(serie, errors="coerce").to_numpy()
    valores = valores[np.isfinite(valores)]

    print(f"\n--- {nome} ---")
    if len(valores) == 0:
        print("Nenhum valor numérico válido.")
        return

    qs = np.percentile(valores, QUANTIS)
    print(f"N válido: {len(valores):,}")
    print(f"Mínimo:   {valores.min():.6g}")
    print(f"Máximo:   {valores.max():.6g}")
    print(f"Média:    {valores.mean():.6g}")
    print(f"Desvio:   {valores.std(ddof=1):.6g}" if len(valores) > 1 else "Desvio: n/a")
    print("Percentis:")
    for q, v in zip(QUANTIS, qs):
        print(f"  P{q:>3}: {v:.6g}")


def histograma(serie, bins, nome):
    valores = pd.to_numeric(serie, errors="coerce").to_numpy()
    valores = valores[np.isfinite(valores)]

    if len(valores) == 0:
        return pd.DataFrame(columns=["limite_inf", "limite_sup", "contagem"])

    contagens, limites = np.histogram(valores, bins=bins)
    return pd.DataFrame({
        "limite_inf": limites[:-1],
        "limite_sup": limites[1:],
        "contagem": contagens,
    })


def main():
    if not ARQUIVO.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO}")

    df = pd.read_csv(ARQUIVO)
    SAIDA.mkdir(parents=True, exist_ok=True)

    print("=" * 68)
    print("AUDITORIA DE SELEÇÃO DO CATÁLOGO")
    print("=" * 68)
    print(f"Arquivo: {ARQUIVO}")
    print(f"Linhas:  {len(df):,}")
    print(f"Colunas: {', '.join(df.columns)}")

    esperadas = ["ra", "dec", "z", "dist_mpc", "modelMag_r"]
    for col in esperadas:
        if col in df.columns:
            resumo(col, df[col])
        else:
            print(f"\n--- {col} ---\nColuna ausente.")

    # Cobertura angular: histogramas marginais e mapa de contagens RA x DEC.
    if {"ra", "dec"}.issubset(df.columns):
        ra = pd.to_numeric(df["ra"], errors="coerce")
        dec = pd.to_numeric(df["dec"], errors="coerce")
        ok = np.isfinite(ra) & np.isfinite(dec)
        sky = pd.DataFrame({"ra": ra[ok], "dec": dec[ok]})

        print("\n--- COBERTURA ANGULAR ---")
        print(f"Coordenadas RA/DEC válidas: {len(sky):,}")
        print(f"RA única (valores distintos): {sky['ra'].nunique():,}")
        print(f"DEC única (valores distintos): {sky['dec'].nunique():,}")

        # Binagem por intervalos observados, útil para detectar lacunas.
        # Não corrige área sólida nem a geometria celeste.
        ra_edges = np.linspace(sky["ra"].min(), sky["ra"].max(),
                               N_BINS_RA + 1)
        dec_edges = np.linspace(sky["dec"].min(), sky["dec"].max(),
                                N_BINS_DEC + 1)

        sky["ra_bin"] = pd.cut(
            sky["ra"], ra_edges, include_lowest=True, labels=False
        )
        sky["dec_bin"] = pd.cut(
            sky["dec"], dec_edges, include_lowest=True, labels=False
        )

        mapa = pd.crosstab(
            sky["dec_bin"], sky["ra_bin"]
        ).reindex(
            index=range(N_BINS_DEC),
            columns=range(N_BINS_RA),
            fill_value=0
        )
        mapa.index.name = "dec_bin"
        mapa.columns.name = "ra_bin"
        mapa.to_csv(SAIDA / "contagens_ra_dec.csv")

        ra_hist = histograma(sky["ra"], ra_edges, "ra")
        dec_hist = histograma(sky["dec"], dec_edges, "dec")
        ra_hist.to_csv(SAIDA / "contagens_ra.csv", index=False)
        dec_hist.to_csv(SAIDA / "contagens_dec.csv", index=False)

        total_bins = N_BINS_RA * N_BINS_DEC
        vazios = int((mapa.to_numpy() == 0).sum())
        print(f"Bins RA x DEC: {total_bins}")
        print(f"Bins sem objetos: {vazios}")
        print(f"Fraçao de bins vazios: {vazios / total_bins:.3f}")
        print("Mapa de contagens salvo em contagens_ra_dec.csv")
        print("A tabela usa bins angulares simples; não é uma máscara oficial.")

    # Distribuição radial e redshift em intervalos iguais de valor.
    for col in ["dist_mpc", "z", "modelMag_r"]:
        if col not in df.columns:
            continue
        valores = pd.to_numeric(df[col], errors="coerce")
        valores = valores[np.isfinite(valores)]
        if len(valores) < 2 or valores.min() == valores.max():
            continue

        tabela = histograma(valores, N_BINS_DIST, col)
        destino = SAIDA / f"contagens_{col}.csv"
        tabela.to_csv(destino, index=False)

        print(f"\n--- CONTAGENS POR INTERVALO: {col} ---")
        print(tabela.to_string(index=False, float_format=lambda x: f"{x:.6g}"))
        print(f"Salvo: {destino}")

    # Diagnóstico conjunto distância x magnitude, se disponível.
    if {"dist_mpc", "modelMag_r"}.issubset(df.columns):
        par = df[["dist_mpc", "modelMag_r"]].apply(
            pd.to_numeric, errors="coerce"
        ).dropna()
        par = par[np.isfinite(par).all(axis=1)]

        if len(par) > 2:
            corr = par.corr(method="spearman").iloc[0, 1]
            print("\n--- DISTÂNCIA x MAGNITUDE ---")
            print(f"Correlação de Spearman: {corr:.5f}")
            print("É uma associação descritiva, não prova de viés por si só.")

    print("\n" + "=" * 68)
    print("LIMITES DESTA AUDITORIA")
    print("=" * 68)
    print("1. Não estima a máscara oficial do levantamento.")
    print("2. Bins vazios podem refletir a geometria da observação.")
    print("3. Contagens iguais em bins não significam densidade física igual.")
    print("4. A magnitude aparente pode ajudar a revelar limites de seleção.")
    print("5. Não calcula FFT, KDE nem testa a hipótese de onda.")
    print(f"\nRelatórios gravados em: {SAIDA}")


if __name__ == "__main__":
    main()
