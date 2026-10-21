import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from astropy.cosmology import FlatLambdaCDM

def espectro_3d(campo, L):
    """
    Espectro radial de um campo 3D em uma caixa cúbica.
    L: lado da caixa em Mpc.
    (Função corrigida pelo Gepeto)
    """
    n = campo.shape[0]
    if campo.shape != (n, n, n):
        raise ValueError("O campo precisa ser uma grade cúbica.")

    # Remover o modo médio (k = 0)
    campo = campo - np.mean(campo)

    # Transformada e potência
    F = np.fft.fftshift(np.fft.fftn(campo))
    power = np.abs(F) ** 2

    # Espaçamento real entre células
    dx = L / n

    # fftfreq retorna ciclos/Mpc; multiplicar por 2π
    freq = np.fft.fftshift(np.fft.fftfreq(n, d=dx))
    k_axis = 2 * np.pi * freq

    KX, KY, KZ = np.meshgrid(k_axis, k_axis, k_axis, indexing="ij")
    K = np.sqrt(KX**2 + KY**2 + KZ**2)

    # Excluir o modo zero
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

def gerar_campo_kde(x, y, z, L, n_grid=64):
    """Gera um campo 3D contínuo via KDE."""
    # Definir a caixa cúbica com lado L
    xmin, xmax = x.min(), x.max()
    ymin, ymax = y.min(), y.max()
    zmin, zmax = z.min(), z.max()
    
    # Ajustar para uma caixa cúbica
    cx, cy, cz = (xmin+xmax)/2, (ymin+ymax)/2, (zmin+zmax)/2
    xmin, xmax = cx - L/2, cx + L/2
    ymin, ymax = cy - L/2, cy + L/2
    zmin, zmax = cz - L/2, cz + L/2

    X_grid, Y_grid, Z_grid = np.mgrid[
        xmin:xmax:n_grid*1j,
        ymin:ymax:n_grid*1j,
        zmin:zmax:n_grid*1j
    ]

    # KDE (usando no máximo 3000 pontos para não travar)
    if len(x) > 3000:
        idx = np.random.choice(len(x), 3000, replace=False)
        x_kde, y_kde, z_kde = x[idx], y[idx], z[idx]
    else:
        x_kde, y_kde, z_kde = x, y, z

    kde = gaussian_kde(np.vstack([x_kde, y_kde, z_kde]), bw_method=0.2)
    pts = np.vstack([X_grid.ravel(), Y_grid.ravel(), Z_grid.ravel()])
    Z_density = kde(pts).reshape(X_grid.shape)
    
    return Z_density

def main():
    print("=== TESTE DO GEPETO: ESPECTRO DE POTÊNCIA 3D ===")
    
    # 1. TESTE SINTÉTICO: Onda de 100 Mpc
    print("[+] Testando FFT com Onda Sintética de 100 Mpc...")
    L = 500.0 # Caixa de 500 Mpc
    n = 64
    k_esperado = 2 * np.pi / 100.0 # 0.0628
    
    # Criar grade
    x = np.linspace(0, L, n)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    onda_sintetica = np.sin(k_esperado * X) # Onda ao longo do eixo X
    
    k_sint, P_sint = espectro_3d(onda_sintetica, L)
    
    # Encontrar o pico
    idx_pico = np.nanargmax(P_sint)
    k_pico = k_sint[idx_pico]
    print(f"    k esperado: {k_esperado:.4f}")
    print(f"    k encontrado: {k_pico:.4f}")
    
    if abs(k_pico - k_esperado) < 0.01:
        print("    -> SUCESSO! A FFT recuperou a onda de 100 Mpc.")
    else:
        print("    -> ERRO! A FFT não encontrou o pico.")
        
    # Plot do teste sintético
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(k_sint, P_sint, 'b-')
    ax1.axvline(k_esperado, color='red', linestyle='--', label='100 Mpc esperado')
    ax1.set_title('Teste de Calibração: Onda Sintética de 100 Mpc')
    ax1.set_xlabel('k (Mpc⁻¹)')
    ax1.set_ylabel('Potência')
    ax1.legend()
    
    pasta = "outputs/reports/galaxias_espectro_potencia"
    os.makedirs(pasta, exist_ok=True)
    plt.savefig(os.path.join(pasta, "teste_sintetico_fft.png"), dpi=120)
    plt.close()
    
    # 2. TESTE REAL: SDSS
    print("\n[+] Calculando Espectro Real (SDSS)...")
    caminho_csv = 'outputs/reports/galaxias_tamanho/dados.csv'
    df = pd.read_csv(caminho_csv)
    df = df[df['modelMag_r'] > 0]
    
    if 'z_mpc' not in df.columns:
        dec_rad = np.radians(df['dec'])
        df['z_mpc'] = df['dist_mpc'] * np.sin(dec_rad)
        
    x_sdss = df['x_mpc'].values
    y_sdss = df['y_mpc'].values
    z_sdss = df['z_mpc'].values
    
    L_real = max(x_sdss.max()-x_sdss.min(), 
                 y_sdss.max()-y_sdss.min(), 
                 z_sdss.max()-z_sdss.min())
    
    campo_real = gerar_campo_kde(x_sdss, y_sdss, z_sdss, L_real, n_grid=64)
    k_real, P_real = espectro_3d(campo_real, L_real)
    
    # 3. CONTROLE NULO
    print("[+] Calculando Espectro Nulo (Random)...")
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
    
    campo_null = gerar_campo_kde(x_rand, y_rand, z_rand_mpc, L_real, n_grid=64)
    k_null, P_null = espectro_3d(campo_null, L_real)
    
    # 4. Plot Final
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.loglog(k_real, P_real, 'b-', label='Dados Reais (SDSS)')
    ax2.loglog(k_null, P_null, 'r--', label='Controle Nulo (Random)')
    
    k_100 = 2 * np.pi / 100
    ax2.axvline(k_100, color='green', linestyle=':', label='100 Mpc (BAO)')
    
    ax2.set_title('Espectro de Potência 3D (Corrigido pelo Gepeto)')
    ax2.set_xlabel('k (Mpc⁻¹)')
    ax2.set_ylabel('Potência P(k)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.savefig(os.path.join(pasta, "espectro_potencia_3d.png"), dpi=120)
    print(f"[+] Salvo em: {pasta}/espectro_potencia_3d.png")

if __name__ == "__main__":
    main()