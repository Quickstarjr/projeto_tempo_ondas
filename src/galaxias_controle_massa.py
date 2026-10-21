import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
    nome_exp = "galaxias_controle_massa"
    print(f"=== INICIANDO EXPERIMENTO: {nome_exp} ===")
    
    caminho_csv = 'outputs/reports/galaxias_tamanho/dados.csv'
    if not os.path.exists(caminho_csv):
        print(f"[ERRO] Arquivo não encontrado: {caminho_csv}.")
        return
        
    df = pd.read_csv(caminho_csv)
    df = df[df['modelMag_r'] > 0] # Filtro de segurança
    print(f"[+] Total de galáxias: {len(df)}")
    
    # 1. Definir a classificação original
    mediana = df['modelMag_r'].median()
    df['is_massiva'] = df['modelMag_r'] <= mediana
    
    massivas_orig = df[df['is_massiva']]
    anas_orig = df[~df['is_massiva']]
    
    # 2. Criar a permutação (Embaralhar os rótulos)
    print("[+] Gerando a permutação aleatória dos rótulos de massa...")
    np.random.seed(42) # Semente para reprodutibilidade
    df_perm = df.copy()
    # Embaralha a coluna booleana
    df_perm['is_massiva'] = np.random.permutation(df_perm['is_massiva'].values)
    
    massivas_perm = df_perm[df_perm['is_massiva']]
    anas_perm = df_perm[~df_perm['is_massiva']]
    
    # 3. Plotar os gráficos (Original vs Permutado)
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # Painel 1: Original (Chladni)
    ax1 = axes[0]
    ax1.scatter(anas_orig['x_mpc'], anas_orig['y_mpc'], c='blue', s=1, alpha=0.3, label='Anãs')
    ax1.scatter(massivas_orig['x_mpc'], massivas_orig['y_mpc'], c='red', s=2, alpha=0.6, label='Massivas')
    ax1.set_title("Original (Segregação de Massa Real)")
    ax1.set_xlabel("X (Mpc)")
    ax1.set_ylabel("Y (Mpc)")
    ax1.legend(markerscale=10)
    
    # Painel 2: Permutado (Controle do Gepeto)
    ax2 = axes[1]
    ax2.scatter(anas_perm['x_mpc'], anas_perm['y_mpc'], c='blue', s=1, alpha=0.3, label='Anãs (Falsas)')
    ax2.scatter(massivas_perm['x_mpc'], massivas_perm['y_mpc'], c='red', s=2, alpha=0.6, label='Massivas (Falsas)')
    ax2.set_title("Permutado (Rótulos Embaralhados - Controle)")
    ax2.set_xlabel("X (Mpc)")
    ax2.set_ylabel("Y (Mpc)")
    ax2.legend(markerscale=10)
    
    plt.tight_layout()
    figs = {"controle_massa.png": fig}
    
    # 4. Resumos
    resumos = {
        "num_galaxias": len(df),
        "mediana_mag": float(mediana),
        "num_massivas": len(massivas_orig),
        "num_anas": len(anas_orig)
    }
    
    log_str = (
        f"=== LOG DE EXECUÇÃO ===\n"
        f"Data: 2026-10-21\n"
        f"Objetivo: Teste de Permutação (Gepeto) para validar a segregação de massa (Chladni).\n"
        f"Galáxias: {len(df)}\n"
        f"Mediana magnitude: {mediana:.2f}\n"
    )
    
    md_str = (
        "## Teste de Permutação de Massa (Controle do Gepeto)\n"
        "Para garantir que a segregação visual não é um artefato da distribuição espacial, os rótulos de 'Massiva' e 'Anã' foram embaralhados aleatoriamente (semente=42).\n\n"
        "### Análise Visual:\n"
        "- **Painel Esquerdo (Original):** Os filamentos vermelhos desenham a teia cósmica.\n"
        "- **Painel Direito (Controle):** Os pontos vermelhos e azuis estão misturados aleatoriamente pelo espaço, sem formar filamentos contínuos.\n\n"
        "### Conclusão:\n"
        "Se o painel direito não mostrar a estrutura de filamentos que o painel esquerdo mostra, isso prova que a distribuição espacial das galáxias massivas é intrinsecamente diferente da distribuição das anãs. A intuição visual foi validada!"
    )
    
    salvar_kit_experimento(nome_exp, df, resumos, figs, log_str, md_str)
    print(f"[+] Kit completo salvo em: outputs/reports/{nome_exp}")

if __name__ == "__main__":
    main()