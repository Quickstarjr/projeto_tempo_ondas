import os
import numpy as np
from scipy.signal import convolve2d
from scipy.stats import norm

def ricker_wavelet(size, sigma):
    x = np.linspace(-size/2, size/2, size)
    y = np.linspace(-size/2, size/2, size)
    X, Y = np.meshgrid(x, y)
    R2 = X**2 + Y**2
    kernel = (1 - R2 / sigma**2) * np.exp(-R2 / (2 * sigma**2))
    return kernel - kernel.mean()

def main():
    print("=== TESTE DE MÉTRICAS REAIS (GEPETO v2) ===")
    N = 400
    x = np.linspace(-1, 1, N)
    y = np.linspace(-1, 1, N)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    Theta = np.arctan2(Y, X)
    
    chladni = np.cos(5 * np.pi * R) * np.cos(3 * Theta)
    chladni = (chladni - chladni.min()) / (chladni.max() - chladni.min())
    kernel = ricker_wavelet(31, sigma=4.0)
    
    # 1. Sinal Observado (Chladni + Ruído)
    rng = np.random.default_rng(42)
    img_chladni = chladni + rng.normal(0, 0.3, (N, N))
    res_chladni = convolve2d(img_chladni, kernel, mode='same', boundary='fill')
    # Métrica: Pico de energia (máximo da resposta)
    metrica_obs = np.max(res_chladni)
    
    # 2. Distribuição Nula (1000 simulações de ruído puro)
    print("[+] Rodando 1000 simulações de ruído puro para o controle nulo...")
    nulas = []
    for i in range(1000):
        ruido = rng.normal(0.5, 0.3, (N, N)) # Média e desvio padrão similares
        res_ruido = convolve2d(ruido, kernel, mode='same', boundary='fill')
        nulas.append(np.max(res_ruido))
        
    nulas = np.array(nulas)
    
    # 3. P-valor (Quantas vezes o ruído superou o sinal?)
    p_valor = np.sum(nulas >= metrica_obs) / 1000
    print(f"\n[+] Pico Observado: {metrica_obs:.4f}")
    print(f"[+] Média do Ruído Nulo: {np.mean(nulas):.4f} ± {np.std(nulas):.4f}")
    print(f"[+] P-valor: {p_valor:.4f}")
    
    if p_valor < 0.05:
        print("    -> Instrumento VALIDADO: p < 0.05.")
    else:
        print("    -> Instrumento NÃO validado: p >= 0.05.")

if __name__ == "__main__":
    main()