import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from scipy.signal import convolve2d
from astropy.cosmology import FlatLambdaCDM

def ricker_wavelet(size, sigma):
    x = np.linspace(-size/2, size/2, size)
    y = np.linspace(-size/2, size/2, size)
    X, Y = np.meshgrid(x, y)
    R2 = X**2 + Y**2
    kernel = (1 - R2 / sigma**2) * np.exp(-R2 / (2 * sigma**2))
    return kernel - kernel.mean()

def main():
    print("=== KDE + WAVELET COM CONTROLE NULO MELHORADO (GEPETO) ===")
    
    caminho_csv = 'outputs/reports/galaxias_tamanho/dados.csv'
    df = pd.read_csv(caminho_csv)
    df = df[df['modelMag_r'] > 0]
    
    # 1. Dados Reais
    x_real = df['x_mpc'].values
    y_real = df['y_mpc'].values
    
    # 2. Controle Nulo: Pontos aleatórios em RA/DEC (respeitando os limites do SDSS)
    # e depois convertidos para X/Y com o mesmo modelo cosmológico
    print("[+] Gerando catálogo de Randoms (Controle Nulo Espacial)...")
    np.random.seed(42)
    n_rand = len(df)
    ra_min, ra_max = df['ra'].min(), df['ra'].max()
    dec_min, dec_max = df['dec'].min(), df['dec'].max()
    
    ra_rand = np.random.uniform(ra_min, ra_max, n_rand)
    dec_rand = np.random.uniform(dec_min, dec_max, n_rand)
    z_rand = np.random.uniform(df['z'].min(), df['z'].max(), n_rand) # Mesma faixa de redshift
    
    cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
    dist_rand = cosmo.comoving_distance(z_rand).value
    ra_rad = np.radians(ra_rand)
    dec_rad = np.radians(dec_rand)
    
    x_rand = dist_rand * np.cos(dec_rad) * np.cos(ra_rad)
    y_rand = dist_rand * np.cos(dec_rad) * np.sin(ra_rad)
    
    # 3. KDE
    print("[+] Calculando KDE (Dados Reais e Randoms)...")
    kde_real = gaussian_kde(np.vstack([x_real, y_real]), bw_method=0.1)
    kde_rand = gaussian_kde(np.vstack([x_rand, y_rand]), bw_method=0.1)
    
    xmin, xmax = x_real.min(), x_real.max()
    ymin, ymax = y_real.min(), y_real.max()
    X, Y = np.mgrid[xmin:xmax:200j, ymin:ymax:200j]
    
    Z_real = kde_real(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)
    Z_rand = kde_rand(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)
    
    # 4. Wavelet
    print("[+] Aplicando Mexican Hat...")
    kernel = ricker_wavelet(31, sigma=4.0)
    W_real = convolve2d(Z_real, kernel, mode='same', boundary='fill')
    W_rand = convolve2d(Z_rand, kernel, mode='same', boundary='fill')
    
    # 5. Métrica: Pico de energia
    metrica_real = np.max(W_real)
    metrica_rand = np.max(W_rand)
    print(f"[+] Pico de Energia (Real): {metrica_real:.4f}")
    print(f"[+] Pico de Energia (Random): {metrica_rand:.4f}")
    
    # 6. Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    vmin, vmax = np.percentile(W_real, [1, 99])
    
    im1 = axes[0].imshow(W_real, origin='lower', extent=[xmin, xmax, ymin, ymax], cmap='RdBu_r', vmin=vmin, vmax=vmax)
    axes[0].set_title("Dados Reais (SDSS)")
    plt.colorbar(im1, ax=axes[0])
    
    im2 = axes[1].imshow(W_rand, origin='lower', extent=[xmin, xmax, ymin, ymax], cmap='RdBu_r', vmin=vmin, vmax=vmax)
    axes[1].set_title("Controle Nulo (Máscara RA/DEC Simulada)")
    plt.colorbar(im2, ax=axes[1])
    
    plt.tight_layout()
    pasta = "outputs/reports/galaxias_kde_controle"
    os.makedirs(pasta, exist_ok=True)
    plt.savefig(os.path.join(pasta, "kde_controle_nulo.png"), dpi=120)
    print(f"[+] Salvo em {pasta}/kde_controle_nulo.png")

if __name__ == "__main__":
    main()