import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import lightkurve as lk

def salvar_kit_experimento(nome_exp, df_dados, dict_resumos, figs, log_texto, md_texto):
    """
    Cria a pasta outputs/reports/<nome_exp> e salva os formatos padronizados.
    figs = dicionário com {'nome_do_arquivo': fig_objeto}
    """
    pasta_exp = os.path.join("outputs", "reports", nome_exp)
    os.makedirs(pasta_exp, exist_ok=True)
    
    # 1. Salvar CSV
    df_dados.to_csv(os.path.join(pasta_exp, "dados.csv"), index=False)
    
    # 2. Salvar JSON
    with open(os.path.join(pasta_exp, "resultado.json"), "w", encoding="utf-8") as f:
        json.dump(dict_resumos, f, indent=2, ensure_ascii=False)
        
    # 3. Salvar LOG
    with open(os.path.join(pasta_exp, "execucao.log"), "w", encoding="utf-8") as f:
        f.write(log_texto)
        
    # 4. Salvar PNGs (nomes descritivos, conforme Grokinha)
    links_raw = []
    for nome_arquivo, fig in figs.items():
        fig.savefig(os.path.join(pasta_exp, nome_arquivo), dpi=120)
        plt.close(fig)
        links_raw.append(f"![{nome_arquivo}](https://raw.githubusercontent.com/Quickstarjr/projeto_tempo_ondas/main/outputs/reports/{nome_exp}/{nome_arquivo})\n")
        
    # 5. Salvar Markdown com os links das imagens
    md_completo = f"# Experimento: {nome_exp}\n\n" + "\n".join(links_raw) + "\n\n" + md_texto
    with open(os.path.join(pasta_exp, "interpretacao.md"), "w", encoding="utf-8") as f:
        f.write(md_completo)
        
    print(f"[+] Kit completo salvo em: {pasta_exp}")

def main():
    nome_exp = "estrela_KIC757450"
    print(f"=== INICIANDO EXPERIMENTO: {nome_exp} ===")
    
    # Baixar dados
    search_result = lk.search_lightcurve("KIC 757450", mission="Kepler")
    lc = search_result.download()
    lc_clean = lc.remove_outliers(sigma=3)
    
    # --- Gerar Gráficos ---
    # 1. Curva de Luz
    fig_luz, ax1 = plt.subplots(figsize=(10, 4))
    lc_clean.plot(ax=ax1)
    ax1.set_title("Curva de Luz - KIC 757450")
    
    # 2. Periodograma Lomb-Scargle
    pg_ls = lc_clean.to_periodogram(method="lombscargle")
    fig_ls, ax2 = plt.subplots(figsize=(10, 4))
    pg_ls.plot(ax=ax2)
    ax2.set_title("Periodograma Lomb-Scargle")
    
    # 3. Periodograma BLS (Trânsitos)
    pg_bls = lc_clean.to_periodogram(method="bls", period=np.arange(1, 20, 0.01))
    fig_bls, ax3 = plt.subplots(figsize=(10, 4))
    pg_bls.plot(ax=ax3)
    ax3.set_title("Periodograma BLS - Busca de Trânsitos")

    figs = {
        "curva_luz.png": fig_luz,
        "periodograma_ls.png": fig_ls,
        "periodograma_bls.png": fig_bls
    }
    
    # --- Salvar Dados (CSV) ---
    df = pd.DataFrame({
        "tempo_bkjd": lc_clean.time.value,
        "fluxo": lc_clean.flux.value
    })
    
    # --- Resumos (JSON) ---
    # Pega o pico mais alto do BLS (se existir)
    periodo_bls = pg_bls.period_at_max_power.value
    potencia_bls = pg_bls.max_power.value
    
    resumos = {
        "estrela": "KIC 757450",
        "missao": "Kepler",
        "num_pontos": len(lc_clean),
        "periodo_bls_dias": float(periodo_bls),
        "potencia_bls": float(potencia_bls)
    }
    
    # --- Log (LOG) ---
    log_str = (
        f"=== EXECUÇÃO ===\n"
        f"Data: 2026-10-20\n"
        f"Alvo: {nome_exp}\n"
        f"Pontos originais: {len(lc)}\n"
        f"Pontos após remover outliers: {len(lc_clean)}\n"
        f"Período BLS detectado: {periodo_bls:.4f} dias\n"
        f"Potência BLS: {potencia_bls:.4e}\n"
    )
    
    # --- Interpretação (Markdown) ---
    md_str = (
        "## Análise Preliminar\n"
        "Este experimento processou os dados brutos da estrela KIC 757450.\n"
        f"O método BLS encontrou um possível trânsito com período de **{periodo_bls:.2f} dias**.\n\n"
        "### Próximos passos\n"
        "Aguardando análise quantitativa do CSV e LOG pelos membros do grupo (Grokinha e Gemini)."
    )
    
    # Salvar tudo
    salvar_kit_experimento(nome_exp, df, resumos, figs, log_str, md_str)

if __name__ == "__main__":
    main()