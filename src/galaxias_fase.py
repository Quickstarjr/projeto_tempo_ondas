import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from astropy.cosmology import FlatLambdaCDM
from astroquery.sdss import SDSS
from astropy import coordinates as coords

# Função padrão do grupo para salvar os resultados
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
        
    print(f"[+] Kit completo salvo em: {pasta_exp}")

def main():
    nome_exp = "galaxias_SDSS_fase"
    print(f"=== INICIANDO EXPERIMENTO: {nome_exp} ===")
    
    # 1. Definir corte espacial e de redshift (ex: uma fatia do céu)
    # Coordenadas aproximadas de uma região do SDSS
    pos = coords.SkyCoord(ra=150, dec=2, unit="deg")
    
    print("Baixando galáxias do SDSS (isso pode demorar um pouco)...")
    # Query no SDSS
    query = """
    SELECT TOP 50000 
      ra, dec, z 
    FROM SpecObj 
    WHERE z BETWEEN 0.05 AND 0.1 
      AND zWarning = 0 
      AND class = 'GALAXY'
      AND ra BETWEEN 140 AND 160 
      AND dec BETWEEN -5 AND 10
    """
    try:
        res = SDSS.query_sql(query)
        df = res.to_pandas()
    except Exception as e:
        print(f"Erro ao baixar do SDSS: {e}")
        return
        
    print(f"[+] Galáxias obtidas: {len(df)}")
    
    # 2. Converter redshift para distância (usando modelo padrão)
    cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
    df['dist_mpc'] = cosmo.comoving_distance(df['z']).value
    
    # Converter RA/DEC/Dist para coordenadas Cartesianas (X, Y, Z)
    ra_rad = np.radians(df['ra'])
    dec_rad = np.radians(df['dec'])
    
    df['x'] = df['dist_mpc'] * np.cos(dec_rad) * np.cos(ra_rad)
    df['y'] = df['dist_mpc'] * np.cos(dec_rad) * np.sin(ra_rad)
    df['z'] = df['dist_mpc'] * np.sin(dec_rad)
    
    # 3. Gerar Gráficos
    # Gráfico 1: Distribuição Espacial (projeção X-Y)
    fig_dist, ax1 = plt.subplots(figsize=(8, 8))
    # Vamos colorir pela distância para dar um efeito 3D
    sc = ax1.scatter(df['x'], df['y'], c=df['dist_mpc'], cmap='viridis', s=1, alpha=0.5)
    ax1.set_title("Distribuição de Galáxias SDSS (Projeção X-Y)")
    ax1.set_xlabel("X (Mpc)")
    ax1.set_ylabel("Y (Mpc)")
    plt.colorbar(sc, ax=ax1, label="Distância (Mpc)")
    
    # Gráfico 2: Espectro de Potência Simplificado (via FFT 2D na projeção)
    # Criar uma grade 2D para a FFT
    bins = 100
    hist, xedges, yedges = np.histogram2d(df['x'], df['y'], bins=bins)
    
    # Fazer a FFT 2D do contraste (subtraindo a média)
    hist_contrast = hist - np.mean(hist)
    fft2 = np.fft.fft2(hist_contrast)
    fft2_shifted = np.fft.fftshift(fft2)
    power = np.abs(fft2_shifted)**2
    
    fig_power, ax2 = plt.subplots(figsize=(8, 6))
    ax2.imshow(np.log1p(power), cmap='inferno', extent=[-bins/2, bins/2, -bins/2, bins/2])
    ax2.set_title("Espectro de Potência 2D (Log)")
    ax2.set_xlabel("k_x")
    ax2.set_ylabel("k_y")
    
    figs = {
        "distribuicao_3d.png": fig_dist,
        "espectro_potencia.png": fig_power
    }
    
    # 4. Resumos (JSON) e Logs
    resumos = {
        "amostra": "SDSS",
        "num_galaxias": len(df),
        "redshift_min": float(df['z'].min()),
        "redshift_max": float(df['z'].max()),
        "dist_min_mpc": float(df['dist_mpc'].min()),
        "dist_max_mpc": float(df['dist_mpc'].max())
    }
    
    log_str = (
        f"=== LOG DE EXECUÇÃO ===\n"
        f"Data: 2026-10-20\n"
        f"Amostra: {len(df)} galáxias do SDSS.\n"
        f"Redshift: {df['z'].min():.3f} a {df['z'].max():.3f}\n"
        f"Modelo Cosmológico: FlatLambdaCDM(H0=70, Om0=0.3)\n"
        f"Conversão para coordenadas cartesianas realizada.\n"
    )
    
    md_str = (
        "## Análise Preliminar da Distribuição de Galáxias\n"
        "Este experimento iniciou a frente de pesquisa sobre a teia cósmica (Etapa A e B do Gepeto).\n"
        "Baixamos uma amostra do SDSS, convertemos para 3D e geramos o espectro de potência 2D.\n"
        "A próxima etapa é aplicar as estatísticas de fase (Line Correlation Function) para verificar a coerência.\n"
    )
    
    salvar_kit_experimento(nome_exp, df, resumos, figs, log_str, md_str)

if __name__ == "__main__":
    main()