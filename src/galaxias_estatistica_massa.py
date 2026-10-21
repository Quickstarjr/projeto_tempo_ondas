import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree

def salvar_kit_experimento(nome_exp, df_dados, dict_resumos, figs, log_texto, md_texto):
    pasta_exp = os.path.join("outputs", "reports", nome_exp)
    os.makedirs(pasta_exp, exist_ok=True)
    if df_dados is not None:
        df_dados.to_csv(os.path.join(pasta_exp, "dados.csv"), index=False)
    with open(os.path.join(pasta_exp, "resultado.json"), "w", encoding="utf-8") as f:
        json.dump(dict_resumos, f, indent=2, ensure_ascii=False)
    with open(os.path.join(pasta_exp, "execucao.log"), "w", encoding="utf-8") as f:
        f.write(log_texto)
    links_raw = []
    for nome_arquivo, fig in figs.items():
        fig.savefig(os.path.join(pasta_exp, nome_arquivo), dpi=120)
        plt.close(fig)
        links_raw.append(f"![{nome_arquivo}](https://raw.githubusercontent.com/Quickstarjr/projeto_tempo_ondas/main/outputs/reports/{nome_exp}/{nome_arquivo})\n")
    md_completo = f"# Experimento: {nome_exp}\n\n" + "\n".join(links_raw) + "\n\n" + md_texto
    with open(os.path.join(pasta_exp, "interpretacao.md"), "w", encoding="utf-8") as f:
        f.write(md_completo)

def main():
    nome_exp = "galaxias_estatistica_massa"
    print(f"=== INICIANDO EXPERIMENTO: {nome_exp} ===")
    
    caminho_csv = 'outputs/reports/galaxias_tamanho/dados.csv'
    if not os.path.exists(caminho_csv):
        print(f"[ERRO] Arquivo não encontrado.")
        return
        
    df = pd.read_csv(caminho_csv)
    df = df[df['modelMag_r'] > 0]
    
    # CORREÇÃO: Reconstruir a coluna z_mpc ANTES de separar os grupos
    if 'z_mpc' not in df.columns:
        print("[!] Reconstruindo z_mpc a partir de dec e dist_mpc...")
        dec_rad = np.radians(df['dec'])
        df['z_mpc'] = df['dist_mpc'] * np.sin(dec_rad)
    
    # Definir classificação (igual ao script anterior)
    mediana = df['modelMag_r'].median()
    df['is_massiva'] = df['modelMag_r'] <= mediana
    
    massivas = df[df['is_massiva']].copy()
    anas = df[~df['is_massiva']].copy()
    
    print(f"[+] Galáxias Massivas: {len(massivas)} | Anãs: {len(anas)}")
    
    # Extrair coordenadas 3D
    coords_massivas = massivas[['x_mpc', 'y_mpc', 'z_mpc']].values
    coords_anas = anas[['x_mpc', 'y_mpc', 'z_mpc']].values
    
    # Calcular distância para o vizinho mais próximo usando cKDTree (rápido)
    print("[+] Calculando distâncias do vizinho mais próximo...")
    tree_massivas = cKDTree(coords_massivas)
    tree_anas = cKDTree(coords_anas)
    
    # k=2 porque o k=1 é a própria galáxia (distância 0)
    dist_massivas, _ = tree_massivas.query(coords_massivas, k=2)
    dist_anas, _ = tree_anas.query(coords_anas, k=2)
    
    # Pegar a coluna 1 (a distância para o vizinho real)
    dist_massivas = dist_massivas[:, 1]
    dist_anas = dist_anas[:, 1]
    
    media_massivas = np.mean(dist_massivas)
    media_anas = np.mean(dist_anas)
    
    print(f"[+] Distância média (Massivas): {media_massivas:.2f} Mpc")
    print(f"[+] Distância média (Anãs): {media_anas:.2f} Mpc")
    
    # Gerar Histograma
    fig, ax = plt.subplots(figsize=(10, 6))
    bins = np.linspace(0, 15, 50) # Focar de 0 a 15 Mpc
    ax.hist(dist_massivas, bins=bins, alpha=0.5, color='red', label='Massivas', density=True)
    ax.hist(dist_anas, bins=bins, alpha=0.5, color='blue', label='Anãs', density=True)
    
    ax.set_title('Distância até o Vizinho Mais Próximo (Galaxy Bias)')
    ax.set_xlabel('Distância (Mpc)')
    ax.set_ylabel('Densidade de Probabilidade')
    ax.legend()
    
    figs = {"histograma_vizinhos.png": fig}
    
    resumos = {
        "dist_media_massivas_Mpc": float(media_massivas),
        "dist_media_anas_Mpc": float(media_anas),
        "diferenca_estatistica_Mpc": float(media_anas - media_massivas)
    }
    
    log_str = (
        f"=== LOG DE EXECUÇÃO ===\n"
        f"Data: 2026-10-21\n"
        f"Distância média ao vizinho mais próximo:\n"
        f"  - Galáxias Massivas: {media_massivas:.2f} Mpc\n"
        f"  - Galáxias Anãs: {media_anas:.2f} Mpc\n"
        f"Diferença (Anãs - Massivas): {resumos['diferenca_estatistica_Mpc']:.2f} Mpc\n"
    )
    
    md_str = (
        "## Estatística do Vizinho Mais Próximo (Galaxy Bias)\n"
        "Para provar que a segregação visual não é um artefato, calculamos a distância de cada galáxia até sua vizinha mais próxima do mesmo tipo.\n\n"
        f"### Resultados:\n"
        f"- **Massivas:** {media_massivas:.2f} Mpc\n"
        f"- **Anãs:** {media_anas:.2f} Mpc\n\n"
        "### Conclusão:\n"
        "Se a distância média das massivas for menor, elas estão mais agrupadas (Galaxy Bias confirmado). A diferença quantitativa valida a intuição visual."
    )
    
    salvar_kit_experimento(nome_exp, df, resumos, figs, log_str, md_str)

if __name__ == "__main__":
    main()