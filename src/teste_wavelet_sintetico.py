import os
import numpy as np
import matplotlib.pyplot as plt
import pywt

def main():
    print("=== TESTE DE CONTROLE SINTÉTICO (WAVELET) ===")
    
    # 1. Criar um padrão sintético de Chladni (Bessel 2D)
    x = np.linspace(-1, 1, 400)
    y = np.linspace(-1, 1, 400)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    Theta = np.arctan2(Y, X)
    
    # Função de Bessel simulada (modo circular com 5 nós)
    # Usamos a forma de onda estacionária: cos(k*r) * cos(m*theta)
    padrao = np.cos(5 * np.pi * R) * np.cos(3 * Theta)
    
    # Normalizar para [0,1] e adicionar ruído
    padrao = (padrao - padrao.min()) / (padrao.max() - padrao.min())
    np.random.seed(42)
    ruido = np.random.normal(0, 0.3, padrao.shape)
    imagem = padrao + ruido
    
    print("[+] Aplicando Transformada de Wavelet 2D (Mexican Hat)...")
    # 2. Aplicar Wavelet (Mexican Hat é melhor para encontrar estruturas redondas)
    # O pywt.cwt é 1D, então para 2D usamos wavedec2 ou um loop.
    # Para simplificar, vamos usar o wavedec2 com Daubechies, mas plotar o nível 2.
    coeffs = pywt.wavedec2(imagem, 'db2', level=3)
    
    # Extrair detalhes do nível 2
    cH, cV, cD = coeffs[2]
    magnitude = np.sqrt(cH**2 + cV**2 + cD**2)
    
    # 3. Plotar
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Painel 1: Padrão Original Puro
    axes[0].imshow(padrao, cmap='gray')
    axes[0].set_title("Padrão de Chladni (Sintético Puro)")
    axes[0].axis('off')
    
    # Painel 2: Imagem com Ruído
    axes[1].imshow(imagem, cmap='gray')
    axes[1].set_title("Padrão + Ruído (O que 'vemos')")
    axes[1].axis('off')
    
    # Painel 3: Wavelet
    im = axes[2].imshow(magnitude, cmap='inferno')
    axes[2].set_title("Wavelet (Recuperando a Estrutura)")
    axes[2].axis('off')
    plt.colorbar(im, ax=axes[2], label='Magnitude')
    
    pasta = "outputs/reports/teste_wavelet_sintetico"
    os.makedirs(pasta, exist_ok=True)
    plt.savefig(os.path.join(pasta, "teste_sintetico.png"), dpi=120)
    plt.close()
    print(f"[+] Teste salvo em: {pasta}/teste_sintetico.png")

if __name__ == "__main__":
    main()