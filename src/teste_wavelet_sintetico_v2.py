import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import convolve2d

def ricker_wavelet(size, sigma):
    """Gera um kernel 2D Mexican Hat (Ricker)."""
    x = np.linspace(-size/2, size/2, size)
    y = np.linspace(-size/2, size/2, size)
    X, Y = np.meshgrid(x, y)
    R2 = X**2 + Y**2
    # Fórmula da Mexican Hat 2D
    kernel = (1 - R2 / sigma**2) * np.exp(-R2 / (2 * sigma**2))
    return kernel - kernel.mean() # Centralizar em zero

def main():
    print("=== TESTE SINTÉTICO v2 (MEXICAN HAT + CONTROLE GEPETO) ===")
    
    # Dimensões
    N = 400
    x = np.linspace(-1, 1, N)
    y = np.linspace(-1, 1, N)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    Theta = np.arctan2(Y, X)
    
    # --- PADRÃO 1: Chladni (Anéis) ---
    chladni = np.cos(5 * np.pi * R) * np.cos(3 * Theta)
    chladni = (chladni - chladni.min()) / (chladni.max() - chladni.min())
    
    # --- PADRÃO 2: Manchas Gaussianas (Aleatório) ---
    rng = np.random.default_rng(42)
    manchas = np.zeros((N, N))
    for _ in range(20): # 20 manchas aleatórias
        cx, cy = rng.uniform(-1, 1, 2)
        blobs = np.exp(-((X-cx)**2 + (Y-cy)**2) / 0.02)
        manchas += blobs
    manchas = (manchas - manchas.min()) / (manchas.max() - manchas.min())
    
    # Adicionar ruído aos dois
    ruido = rng.normal(0, 0.3, (N, N))
    img_chladni = chladni + ruido
    img_manchas = manchas + ruido
    
    # --- APLICAR MEXICAN HAT ---
    # Tamanho do kernel e sigma (escala de detecção)
    kernel_size = 31
    kernel = ricker_wavelet(kernel_size, sigma=4.0)
    
    print("[+] Aplicando a Mexican Hat no padrão de Chladni...")
    res_chladni = convolve2d(img_chladni, kernel, mode='same', boundary='fill')
    
    print("[+] Aplicando a Mexican Hat no padrão de Manchas...")
    res_manchas = convolve2d(img_manchas, kernel, mode='same', boundary='fill')
    
    # --- PLOTAGEM ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # Linha 1: Chladni
    axes[0, 0].imshow(img_chladni, cmap='gray')
    axes[0, 0].set_title("Chladni + Ruído")
    axes[0, 0].axis('off')
    
    im1 = axes[0, 1].imshow(res_chladni, cmap='RdBu_r', vmin=-0.1, vmax=0.1)
    axes[0, 1].set_title("Mexican Hat (Detectando Anéis)")
    axes[0, 1].axis('off')
    
    # Linha 2: Manchas
    axes[1, 0].imshow(img_manchas, cmap='gray')
    axes[1, 0].set_title("Manchas + Ruído")
    axes[1, 0].axis('off')
    
    im2 = axes[1, 1].imshow(res_manchas, cmap='RdBu_r', vmin=-0.1, vmax=0.1)
    axes[1, 1].set_title("Mexican Hat (Detectando Bolhas)")
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    pasta = "outputs/reports/teste_wavelet_sintetico_v2"
    os.makedirs(pasta, exist_ok=True)
    plt.savefig(os.path.join(pasta, "teste_sintetico_v2.png"), dpi=120)
    plt.close()
    print(f"[+] Teste salvo em: {pasta}/teste_sintetico_v2.png")

if __name__ == "__main__":
    main()