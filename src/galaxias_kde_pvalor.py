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

def calcular_pico_kde_wavelet(x, y, X_grid, Y_grid, kernel):
    kde = gaussian_kde(np.vstack([x, y]), bw_method=0.1)
    Z = kde(np.vstack([X_grid.ravel(), Y_grid.ravel()])).reshape(X_grid.shape)
    W = convolve2d(Z, kernel, mode='same', boundary='fill')
    return np.max(W)

def main():
    print("=== VALIDAÇÃO FINAL (GEPETO v3): P-VALOR VIA MONTE CARLO ===")
    
    caminho_csv = 'outputs/reports/galaxias_tamanho/dados.csv'
    df = pd.read_csv(caminho_csv)
    df = df[df['modelMag_r'] > 0]
    
    # Dados Reais
    x_real = df['x_mpc'].values
    y_real = df['y_mpc'].values
    ra_min, ra_max = df['ra'].min(), df['ra'].max()
    dec_min, dec_max = df['dec'].min(), df['dec'].max()
    z_min, z_max = df['z'].min(), df['z'].max()
    cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
    
    # Grade e Kernel
    xmin, xmax = x_real.min(), x_real.max()
    ymin, ymax = y_real.min(), y_real.max()
    X_grid, Y_grid = np.mgrid[xmin:xmax:100j, ymin:ymax:100j] # Grade menor para ser mais rápido
    kernel = ricker_wavelet(31, sigma=4.0)
    
    # 1. Pico Real
    print("[+] Calculando Pico Real (SDSS)...")
    pico_real = calcular_pico_kde_wavelet(x_real, y_real, X_grid, Y_grid, kernel)
    print(f"    Pico Real: {pico_real:.6f}")
    
    # 2. Picos Nulos (N=100)
    N_SIMULACOES = 100
    print(f"[+] Rodando {N_SIMULACOES} simulações de catálogos nulos (RA/DEC/Z aleatórios)...")
    picos_nulos = []
    
    np.random.seed(42)
    for i in range(N_SIMULACOES):
        ra_rand = np.random.uniform(ra_min, ra_max, len(df))
        dec_rand = np.random.uniform(dec_min, dec_max, len(df))
        z_rand = np.random.uniform(z_min, z_max, len(df))
        
        dist_rand = cosmo.comoving_distance(z_rand).value
        ra_rad = np.radians(ra_rand)
        dec_rad = np.radians(dec_rand)
        x_rand = dist_rand * np.cos(dec_rad) * np.cos(ra_rad)
        y_rand = dist_rand * np.cos(dec_rad) * np.sin(ra_rad)
        
        pico_nulo = calcular_pico_kde_wavelet(x_rand, y_rand, X_grid, Y_grid, kernel)
        picos_nulos.append(pico_nulo)
        
        if (i+1) % 20 == 0:
            print(f"    {i+1}/{N_SIMULACOES}...")
            
    picos_nulos = np.array(picos_nulos)
    
    # 3. P-valor (Fórmula do Gepeto)
    k = np.sum(picos_nulos >= pico_real)
    p_valor = (k + 1) / (N_SIMULACOES + 1)
    
    print(f"\n[+] Média dos picos nulos: {np.mean(picos_nulos):.6f} ± {np.std(picos_nulos):.6f}")
    print(f"[+] Pico real: {pico_real:.6f}")
    print(f"[+] P-valor (fórmula do Gepeto): {p_valor:.4f}")
    
    if p_valor < 0.05:
        print("    -> DADOS REAIS SÃO ESTATISTICAMENTE INCOMUNS (p < 0.05)")
    else:
        print("    -> DADOS REAIS NÃO SÃO ESTATISTICAMENTE INCOMUNS")
        
    # 4. Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(picos_nulos, bins=20, color='gray', alpha=0.7, label='Distribuição Nula')
    ax.axvline(pico_real, color='red', linestyle='--', linewidth=2, label=f'Pico Real = {pico_real:.6f}')
    ax.set_title('Validação do Chladni Cósmico via Monte Carlo')
    ax.set_xlabel('Pico de Energia da Wavelet')
    ax.set_ylabel('Frequência')
    ax.legend()
    
    pasta = "outputs/reports/galaxias_kde_pvalor"
    os.makedirs(pasta, exist_ok=True)
    plt.savefig(os.path.join(pasta, "pvalor_montecarlo.png"), dpi=120)
    print(f"[+] Gráfico salvo em: {pasta}/pvalor_montecarlo.png")

if __name__ == "__main__":
    main()