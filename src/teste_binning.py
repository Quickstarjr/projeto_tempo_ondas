import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Importa as funções do pipeline_real (que já tem a lógica de correlação)
sys.path.append('.')
from src.pipeline_real import calcular_pares, binnar_por_theta, reamostrar_por_bin

# Carrega os dados reais
df = pd.read_csv('data/synthetic/nanograv_15yr.csv')
df_reamostrado = reamostrar_por_bin(df, bin_dias=30)
df_pares = calcular_pares(df_reamostrado, df, min_overlap=10)

# Testa 10 bins e 20 bins
bins_10 = binnar_por_theta(df_pares, n_bins=10)
bins_20 = binnar_por_theta(df_pares, n_bins=20)

# Plota a comparação
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Painel 1: 10 bins
axes[0].errorbar(bins_10['theta_medio'], bins_10['corr_media'], 
                 yerr=bins_10['corr_erro'], fmt='o-', capsize=3, label='10 bins')
axes[0].plot(bins_10['theta_medio'], bins_10['hd_medio'], 'g--', label='HD')
axes[0].set_title('Análise com 10 Bins (Original)')
axes[0].set_xlabel('θ (graus)')
axes[0].set_ylabel('Correlação')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Painel 2: 20 bins
axes[1].errorbar(bins_20['theta_medio'], bins_20['corr_media'], 
                 yerr=bins_20['corr_erro'], fmt='o-', capsize=3, label='20 bins')
axes[1].plot(bins_20['theta_medio'], bins_20['hd_medio'], 'g--', label='HD')
axes[1].set_title('Análise com 20 Bins (Teste Gepeto)')
axes[1].set_xlabel('θ (graus)')
axes[1].set_ylabel('Correlação')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/plots/comparacao_bins_10_vs_20.png', dpi=120)
print("[+] Gráfico salvo em outputs/plots/comparacao_bins_10_vs_20.png")