import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from astropy.cosmology import FlatLambdaCDM
from astroquery.sdss import SDSS

def salvar_kit_experimento(nome_exp, df_dados, dict_resumos, figs, log_texto, md_texto):
    pasta_exp = os.path.join("outputs", "reports", nome_exp)
    os.makedirs(pasta_exp, exist_ok=True)
    df_dados.to_csv(os.path.join(pasta_exp, "dados.csv"), index=False)
    with open(os.path.join(pasta_exp, "resultado.json"), "w", encoding="utf-8") as f:
        json.dump(dict_resumos, f, indent=2, ensure_ascii=False)
    with open(os.path.join(pasta_exp, "execucao.log"), "w", encoding="utf-8") as f:
        f.write(log_texto)
    links_raw = []
    for nome_arquivo, fig in figs.items():
        fig.savefig(os.path.join(pasta_exp, nome_arquivo), dpi=120)
        plt.close(fig)
        links_raw.append(f"![{nome_arquivo}](https://raw.githubusercontent.com/Quickstarjr/projeto_tempo_ondas/main/outputs/reports/{nome_exp}/{nome_arquivo})\n")
    md_completo = f"# Experimento: {nome_exp}\n\n" + "\n".join(links_raw) + "\n\n" + md_texto
    with open(os.path.join(pasta_exp, "interpretacao.md"), "w", encoding="utf-8") as f:
        f.write(md_completo)

def main():
    nome_exp = "galaxias_tamanho"
    print(f"=== INICIANDO EXPERIMENTO: {nome_exp} ===")
    
    # Correção definitiva: usar a tabela SpecPhoto
    query = """
    SELECT TOP 50000 
      ra, dec, z, modelMag_r
    FROM SpecPhoto 
    WHERE z BETWEEN 0.05 AND 0.1 
      AND zWarning = 0 
      AND class = 'GALAXY'
      AND ra BETWEEN 140 AND 160 
      AND dec BETWEEN -5 AND 10
       AND modelMag_r > 0 
    """
    try:
        res = SDSS.query_sql(query)
        df = res.to_pandas()
    except Exception as e:
        print(f"Erro ao baixar do SDSS: {e}")
        return
        
    print(f"[+] Galáxias obtidas: {len(df)}")
    
    cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
    df['dist_mpc'] = cosmo.comoving_distance(df['z']).value
    
    ra_rad = np.radians(df['ra'])
    dec_rad = np.radians(df['dec'])
    df['x_mpc'] = df['dist_mpc'] * np.cos(dec_rad) * np.cos(ra_rad)
    df['y_mpc'] = df['dist_mpc'] * np.cos(dec_rad) * np.sin(ra_rad)
    
    # --- A MÁGICA DA ANALOGIA DE CHLADNI ---
    mediana_mag = df['modelMag_r'].median()
    print(f"[+] Mediana da magnitude (modelMag_r): {mediana_mag:.2f}")
    
    massivas = df[df['modelMag_r'] <= mediana_mag]
    anas = df[df['modelMag_r'] > mediana_mag]
    
    print(f"    - Galáxias Massivas (Grãos Grandes): {len(massivas)}")
    print(f"    - Galáxias Anãs (Grãos Finos): {len(anas)}")
    
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.scatter(anas['x_mpc'], anas['y_mpc'], c='blue', s=1, alpha=0.3, label='Anãs (Grãos Finos)')
    ax.scatter(massivas['x_mpc'], massivas['y_mpc'], c='red', s=2, alpha=0.6, label='Massivas (Grãos Grandes)')
    
    ax.set_title("Analogia de Chladni: Segregação de Massa na Teia Cósmica")
    ax.set_xlabel("X (Mpc)")
    ax.set_ylabel("Y (Mpc)")
    ax.legend(markerscale=10)
    
    figs = {"segregacao_massa.png": fig}
    
    resumos = {
        "num_galaxias": len(df),
        "magnitude_mediana": float(mediana_mag),
        "num_massivas": len(massivas),
        "num_anas": len(anas)
    }
    
    log_str = (
        f"=== LOG DE EXECUÇÃO ===\n"
        f"Data: 2026-10-20\n"
        f"Magnitude mediana (modelMag_r): {mediana_mag:.2f}\n"
        f"Galáxias Massivas: {len(massivas)}\n"
        f"Galáxias Anãs: {len(anas)}\n"
        f"Fonte: Tabela SpecPhoto do SDSS.\n"
        f"Objetivo: Testar a analogia de Chladni (grão grande vs fino) na Cosmic Web.\n"
    )
    
    md_str = (
        "## Analogia de Chladni: O Tamanho do Grão Cósmico\n"
        "Inspirado pela intuição do Quickstar sobre os experimentos de Chladni, dividimos as galáxias "
        "do SDSS em dois grupos com base na magnitude (brilho): as massivas (grãos grandes) e as anãs (grãos finos).\n\n"
        "### Discussão do Grupo:\n"
        "- **Gemini:** Explicou o Galaxy Bias ($b$). Galáxias massivas têm $b \\gg 2$ e traçam os super-nós. Anãs têm $b \\approx 1$ e preenchem filamentos e vazios.\n"
        "- **Gepeto:** Propôs três hipóteses (H0: sem efeito; H1: efeito de tamanho; H2: assinatura ondulatória). Alertou sobre efeitos de seleção (Malmquist bias).\n"
        "- **Grokinha:** Reforçou a analogia com grãos grandes vs pó de licopódio e sugeriu separar por espectro de potência.\n\n"
        "### O que esperar:\n"
        "Na física de Chladni, grãos maiores tendem a se acumular nos nós, enquanto os finos ficam nos ventres. "
        "Na cosmologia, espera-se que as galáxias massivas (vermelhas) se concentrem nos nós da teia cósmica (aglomerados), "
        "enquanto as anãs (azuis) se espalhem mais pelos filamentos e vazios."
    )
    
    salvar_kit_experimento(nome_exp, df, resumos, figs, log_str, md_str)
    print(f"[+] Kit completo salvo em: outputs/reports/{nome_exp}")

if __name__ == "__main__":
    main()