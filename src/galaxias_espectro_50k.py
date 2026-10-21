import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from astropy.cosmology import FlatLambdaCDM

def espectro_3d(campo, L):
    n = campo.shape[0]
    campo = campo - np.mean(campo)
    F = np.fft.fftshift(np.fft.fftn(campo))
    power = np.abs(F) ** 2
    dx = L / n
    freq = np.fft.fftshift(np.fft.fftfreq(n, d=dx))
    k_axis = 2 * np.pi * freq
    KX, KY, KZ = np.meshgrid(k_axis, k_axis, k_axis, indexing="ij")
    K = np.sqrt(KX**2 + KY**2 + KZ**2)
    valid = K > 0
    
    k_bins = np.linspace(0, K.max(), 40)
    indices = np.digitize(K[valid], k_bins) - 1
    k_centers = 0.5 * (k_bins[:-1] + k_bins[1:])
    power_avg = np.full(len(k_centers), np.nan)
    
    for i in range(len(k_centers)):
        mask = indices == i
        if np.any(mask):
            power_avg[i] = np.mean(power[valid][mask])
    return k_centers, power_avg

def criar_campo_histograma(x, y, z, L, n_grid=128, smooth_sigma=2):
    # 1. Definir os limites da caixa
    xmin, xmax = x.min(), x.max()
    ymin, ymax = y.min(), y.max()
    zmin, zmax = z.min(), z.max()
    
    cx, cy, cz = (xmin+xmax)/2, (ymin+ymax)/2, (zmin+zmax)/2
    xmin, xmax = cx - L/2, cx + L/2
    ymin, ymax = cy - L/2, cy + L/2
    zmin, zmax = cz - L/2, cz + L/2
    
    # 2. Histograma 3D
    hist, _ = np.histogramdd((x, y, z), bins=(n_grid, n_grid, n_grid), 
                             range=((xmin, xmax), (ymin, ymax), (zmin, zmax)))
    
    # 3. Suavização Gaussiana (KDE rápido)
    campo = gaussian_filter(hist.astype(float), sigma=smooth_sigma)
    return campo

def main():
    print("=== ESPECTRO DE POTÊNCIA 3D (50.000 GALÁXIAS) ===")
    caminho_csv = 'data/processed/galaxias_50k.csv'
    if not os.path.exists(caminho_csv):
        print(f"[ERRO] Arquivo {caminho_csv} não encontrado. Rode o download primeiro.")
        return
        
    df = pd.read_csv(caminho_csv)
    print(f"[+] Galáxias carregadas: {len(df)}")
    
    # Coordenadas
    dec_rad = np.radians(df['dec'])
    df['z_mpc'] = df['dist_mpc'] * np.sin(dec_rad) if 'dist_mpc' in df.columns else None
    
    # Calcular distâncias se não existirem
    if 'dist_mpc' not in df.columns:
        cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
        df['dist_mpc'] = cosmo.comoving_distance(df['z']).value
        dec_rad = np.radians(df['dec'])
        df['z_mpc'] = df['dist_mpc'] * np.sin(dec_rad)
        
    ra_rad = np.radians(df['ra'])
    df['x_mpc'] = df['dist_mpc'] * np.cos(dec_rad) * np.cos(ra_rad)
    df['y_mpc'] = df['dist_mpc'] * np.cos(dec_rad) * np.sin(ra_rad)
    
    x = df['x_mpc'].values
    y = df['y_mpc'].values
    z = df['z_mpc'].values
    
    L = max(x.max()-x.min(), y.max()-y.min(), z.max()-z.min())
    print(f"[+] Lado da caixa (L): {L:.1f} Mpc")
    
    # Campo Real
    print("[+] Gerando campo de densidade real (128x128x128)...")
    campo_real = criar_campo_histograma(x, y, z, L, n_grid=128, smooth_sigma=2)
    k_real, P_real = espectro_3d(campo_real, L)
    
    # Campo Nulo (Random)
    print("[+] Gerando campo de densidade nulo...")
    np.random.seed(42)
    ra_rand = np.random.uniform(df['ra'].min(), df['ra'].max(), len(df))
    dec_rand = np.random.uniform(df['dec'].min(), df['dec'].max(), len(df))
    z_rand = np.random.uniform(df['z'].min(), df['z'].max(), len(df))
    
    cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
    dist_rand = cosmo.comoving_distance(z_rand).value
    ra_rad = np.radians(ra_rand)
    dec_rad = np.radians(dec_rand)
    x_rand = dist_rand * np.cos(dec_rad) * np.cos(ra_rad)
    y_rand = dist_rand * np.cos(dec_rad) * np.sin(ra_rad)
    z_rand_mpc = dist_rand * np.sin(dec_rad)
    
    campo_null = criar_campo_histograma(x_rand, y_rand, z_rand_mpc, L, n_grid=128, smooth_sigma=2)
    k_null, P_null = espectro_3d(campo_null, L)
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.loglog(k_real, P_real, 'b-', label='Dados Reais (50k Galáxias)')
    ax.loglog(k_null, P_null, 'r--', label='Controle Nulo (Random)')
    
    k_100 = 2 * np.pi / 100
    ax.axvline(k_100, color='green', linestyle=':', label='100 Mpc (BAO)')
    
    ax.set_title('Espectro de Potência 3D - Massivo (50k Galáxias)')
    ax.set_xlabel('k (Mpc⁻¹)')
    ax.set_ylabel('Potência P(k)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    pasta = "outputs/reports/galaxias_espectro_50k"
    os.makedirs(pasta, exist_ok=True)
    plt.savefig(os.path.join(pasta, "espectro_50k.png"), dpi=120)
    print(f"[+] Salvo em: {pasta}/espectro_50k.png")

if __name__ == "__main__":
    main()