import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree

def main():
    print("=== TESTE DE PERMUTAÇÃO (GEPETO) ===")
    caminho_csv = 'outputs/reports/galaxias_tamanho/dados.csv'
    df = pd.read_csv(caminho_csv)
    df = df[df['modelMag_r'] > 0]
    
    # Reconstruir z_mpc
    if 'z_mpc' not in df.columns:
        dec_rad = np.radians(df['dec'])
        df['z_mpc'] = df['dist_mpc'] * np.sin(dec_rad)
        
    coords = df[['x_mpc', 'y_mpc', 'z_mpc']].values
    mags = df['modelMag_r'].values
    
    def calcular_delta(mags_perm):
        mediana = np.median(mags_perm)
        is_massiva = mags_perm <= mediana
        massivas = coords[is_massiva]
        anas = coords[~is_massiva]
        
        tree_m = cKDTree(massivas)
        tree_a = cKDTree(anas)
        
        dist_m, _ = tree_m.query(massivas, k=2)
        dist_a, _ = tree_a.query(anas, k=2)
        
        return np.mean(dist_a[:, 1]) - np.mean(dist_m[:, 1])
    
    # 1. Delta Observado
    delta_obs = calcular_delta(mags)
    print(f"[+] Delta Observado (Anãs - Massivas): {delta_obs:.4f} Mpc")
    
    # 2. Teste de Permutação
    N_PERM = 10000
    print(f"[+] Rodando {N_PERM} permutações... (Isso pode levar alguns minutos)")
    deltas_perm = []
    
    np.random.seed(42)
    for i in range(N_PERM):
        mags_perm = np.random.permutation(mags)
        deltas_perm.append(calcular_delta(mags_perm))
        if (i+1) % 2000 == 0:
            print(f"    {i+1}/{N_PERM}...")
            
    deltas_perm = np.array(deltas_perm)
    
    # 3. P-valor
    p_valor = np.sum(deltas_perm >= delta_obs) / N_PERM
    print(f"\n[+] P-valor: {p_valor:.5f}")
    if p_valor < 0.05:
        print("    -> Diferença ESTATISTICAMENTE SIGNIFICATIVA (p < 0.05)")
    else:
        print("    -> Diferença NÃO é significativa (p >= 0.05)")
        
    # 4. Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(deltas_perm, bins=50, color='gray', alpha=0.7, label='Distribuição Nula (Permutada)')
    ax.axvline(delta_obs, color='red', linestyle='--', linewidth=2, label=f'Observado = {delta_obs:.3f} Mpc')
    ax.set_title('Teste de Permutação - Diferença de Vizinhança (Galaxy Bias)')
    ax.set_xlabel('Δ (Distância Anãs - Distância Massivas) [Mpc]')
    ax.set_ylabel('Frequência')
    ax.legend()
    
    pasta = "outputs/reports/galaxias_teste_permutacao"
    os.makedirs(pasta, exist_ok=True)
    plt.savefig(os.path.join(pasta, "histograma_nulo.png"), dpi=120)
    plt.close()
    
    # Salvar resultados
    with open(os.path.join(pasta, "resultado.json"), "w") as f:
        json.dump({"delta_obs": delta_obs, "p_valor": p_valor, "N_perm": N_PERM}, f, indent=2)

if __name__ == "__main__":
    main()