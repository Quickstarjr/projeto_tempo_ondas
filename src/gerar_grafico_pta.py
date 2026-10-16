import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def curva_hellings_downs(theta_deg):
    """
    Calcula a curva teórica de Hellings-Downs para um fundo isotrópico.
    """
    x = (1 - np.cos(np.radians(theta_deg))) / 2.0
    # Evita log(0) se theta = 0
    x = np.where(x == 0, 1e-9, x)
    return 0.5 - 0.25 * x + 1.5 * x * np.log(x)

# 1. Carregar os pares calculados pelo script anterior
df_pares = pd.read_csv("correlacao_pares_pta.csv")

# 2. Gerar curva teórica
theta_grid = np.linspace(0.1, 180, 200)
hd_teorico = curva_hellings_downs(theta_grid)

# 3. Plotar os dados
plt.figure(figsize=(10, 6))
plt.scatter(df_pares['theta_deg'], df_pares['correlacao_residuos'], 
            alpha=0.6, color='indigo', label='Pares de Pulsares (Sintéticos)')

plt.plot(theta_grid, hd_teorico, color='crimson', linewidth=2, linestyle='--', 
         label='Curva de Hellings-Downs (Teórica RG)')

plt.axhline(0, color='gray', linestyle=':', alpha=0.7)
plt.title("Amostra PTA: Correlação de Resíduos vs. Separação Angular (\u03b8)")
plt.xlabel("Separação Angular \u03b8 (graus)")
plt.ylabel("Correlação Cruzada dos Resíduos")
plt.grid(True, alpha=0.3)
plt.legend()

# 4. Salvar gráfico em imagem
nome_grafico = "grafico_correlacao_pta.png"
plt.savefig(nome_grafico, dpi=300)
print(f"[+] Gráfico salvo com sucesso em: {nome_grafico}")
plt.show()