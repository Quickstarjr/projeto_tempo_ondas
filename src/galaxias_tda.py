import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ripser import ripser

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
    nome_exp = "galaxias_tda"
    print(f"=== INICIANDO EXPERIMENTO: {nome_exp} ===")
    
    # 1. Carregar os dados do experimento anterior
    caminho_csv = 'outputs/reports/galaxias_tamanho/dados.csv'
    if not os.path.exists(caminho_csv):
        print(f"[ERRO] Arquivo não encontrado: {caminho_csv}. Rode o galaxias_tamanho.py primeiro.")
        return
        
    df = pd.read_csv(caminho_csv)
    print(f"[+] Total de galáxias carregadas: {len(df)}")
    
    # CORREÇÃO: Reconstruir a coordenada z_mpc que não foi salva no CSV anterior
    if 'z_mpc' not in df.columns:
        print("[!] Coluna 'z_mpc' não encontrada. Reconstruindo a partir da distância e declinação...")
        dec_rad = np.radians(df['dec'])
        df['z_mpc'] = df['dist_mpc'] * np.sin(dec_rad)
    
    # 2. Filtrar coordenadas válidas e amostrar (TDA em 3D é pesado)
    df = df.dropna(subset=['x_mpc', 'y_mpc', 'z_mpc'])
    N_AMOSTRA = 1500 # Amostragem para manter o cálculo rápido na CPU
    if len(df) > N_AMOSTRA:
        df_amostra = df.sample(n=N_AMOSTRA, random_state=42)
    else:
        df_amostra = df
        
    print(f"[+] Amostra para TDA: {len(df_amostra)} galáxias")
    
    # Extrair coordenadas 3D
    X = df_amostra[['x_mpc', 'y_mpc', 'z_mpc']].values
    
    # 3. Calcular Homologia Persistente com Ripser
    print("[+] Calculando Homologia Persistente (H0 e H1)... (Isso pode levar 1-2 minutos)")
    result = ripser(X, maxdim=1)
    dgms = result['dgms']
    
    # 4. Gerar Gráficos
    # Gráfico 1: Diagrama de Persistência
    fig_pers, ax1 = plt.subplots(figsize=(8, 6))
    # Plotar H0 (azul) e H1 (vermelho)
    for dim, color, label in zip([0, 1], ['blue', 'red'], ['H0 (Componentes)', 'H1 (Buracos/Anéis)']):
        dgm = dgms[dim]
        # Ignorar pontos com morte infinita no plot
        finite_dgm = dgm[np.isfinite(dgm[:, 1])]
        if len(finite_dgm) > 0:
            ax1.scatter(finite_dgm[:, 0], finite_dgm[:, 1], c=color, label=label, alpha=0.6, s=10)
    
    ax1.plot([0, 500], [0, 500], 'k--', alpha=0.5, label='Diagonal (ruído)')
    ax1.set_xlabel('Nascimento (Mpc)')
    ax1.set_ylabel('Morte (Mpc)')
    ax1.set_title('Diagrama de Persistência - SDSS')
    ax1.legend()
    
    # Gráfico 2: Curva de Betti (H1)
    fig_betti, ax2 = plt.subplots(figsize=(8, 5))
    # Definir grid de raios (epsilons) de 0 até 150 Mpc
    epsilons = np.linspace(0, 150, 100)
    
    # Calcular H0 e H1 ao longo de epsilon
    betti_0 = [np.sum((dgms[0][:, 0] <= e) & (dgms[0][:, 1] > e)) for e in epsilons]
    betti_1 = [np.sum((dgms[1][:, 0] <= e) & (dgms[1][:, 1] > e)) for e in epsilons]
    
    ax2.plot(epsilons, betti_1, c='red', lw=2, label='Curva de Betti H1 (Anéis)')
    ax2.plot(epsilons, betti_0, c='blue', lw=1, alpha=0.5, label='Curva de Betti H0 (Componentes)')
    ax2.set_xlabel('Escala de distância ε (Mpc)')
    ax2.set_ylabel('Número de características topológicas')
    ax2.set_title('Curvas de Betti - Estrutura da Teia Cósmica')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    figs = {
        "diagrama_persistencia.png": fig_pers,
        "curva_betti.png": fig_betti
    }
    
    # 5. Resumos (JSON)
    resumos = {
        "num_galaxias_originais": len(df),
        "num_galaxias_amostra": len(df_amostra),
        "max_aneis_H1_simultaneos": int(max(betti_1)),
        "escala_pico_H1_Mpc": float(epsilons[np.argmax(betti_1)])
    }
    
    log_str = (
        f"=== LOG DE EXECUÇÃO ===\n"
        f"Data: 2026-10-20\n"
        f"Entrada: {caminho_csv}\n"
        f"Galáxias processadas na TDA: {len(df_amostra)}\n"
        f"Pico de H1: {resumos['max_aneis_H1_simultaneos']} anéis em ε={resumos['escala_pico_H1_Mpc']:.1f} Mpc\n"
        f"Objetivo: Medir a topologia da Cosmic Web para validar os nós de Chladni.\n"
    )
    
    md_str = (
        "## Análise Topológica de Dados (TDA)\n"
        "Este experimento aplicou Homologia Persistente nos dados do SDSS para quantificar a estrutura da teia cósmica.\n"
        "O **Diagrama de Persistência** mostra quais estruturas sobrevivem ao longo das escalas (pontos longe da diagonal).\n"
        "A **Curva de Betti H1** conta quantos anéis topológicos existem em cada escala. Se a Grande Onda estiver estruturada como as Figuras de Chladni, devemos ver picos claros nesta curva.\n\n"
        "### Próximos passos:\n"
        "Comparar esta curva com um catálogo de pontos aleatórios (Monte Carlo) para provar que a estrutura não é ruído."
    )
    
    salvar_kit_experimento(nome_exp, df_amostra, resumos, figs, log_str, md_str)
    print(f"[+] Kit completo salvo em: outputs/reports/{nome_exp}")

if __name__ == "__main__":
    main()