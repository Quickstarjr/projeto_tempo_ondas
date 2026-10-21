import os
import numpy as np
import matplotlib.pyplot as plt
from astroquery.skyview import SkyView
import pywt
import json

def salvar_kit_experimento(nome_exp, dict_resumos, figs, log_texto, md_texto):
    pasta_exp = os.path.join("outputs", "reports", nome_exp)
    os.makedirs(pasta_exp, exist_ok=True)
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
    nome_exp = "nebulosa_wavelets"
    print(f"=== INICIANDO TESTE DE CONTROLE: {nome_exp} ===")
    
    # 1. Baixar imagem da Nebulosa de Órion (SkyView)
    print("[+] Baixando imagem da Nebulosa de Órion (SkyView)...")
    # Coordenadas centrais de Órion: RA 83.82, Dec -5.39
    try:
        images = SkyView.get_images(position='Orion Nebula', survey=['DSS2 Red'], pixels=300)
        hdu = images[0][0]
        data = hdu.data
        if data is None:
            raise ValueError("Dados da imagem vazios.")
    except Exception as e:
        print(f"[ERRO] Falha ao baixar imagem: {e}")
        return
        
    # Normalizar os dados para [0, 1] e remover NaNs
    data = np.nan_to_num(data.astype(float))
    data = (data - data.min()) / (data.max() - data.min())
    print(f"[+] Imagem carregada: {data.shape[0]}x{data.shape[1]} pixels")
    
    # 2. Aplicar a Transformada de Wavelet 2D (Daubechies 1)
    print("[+] Aplicando Transformada de Wavelet 2D...")
    wavelet = 'db1'
    coeffs = pywt.wavedec2(data, wavelet, level=4)
    
    # Extrair os coeficientes de detalhe (as estruturas em cada escala)
    # coeffs[0] = aproximação, coeffs[1] = detalhes nível 1, etc.
    # Vamos plotar o detalhe do nível 3 (escala média)
    detail_level = 3
    cH, cV, cD = coeffs[detail_level]
    magnitude = np.sqrt(cH**2 + cV**2 + cD**2)
    
    # 3. Gerar Gráficos
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Painel 1: Imagem Original
    ax1 = axes[0]
    ax1.imshow(data, cmap='gray')
    ax1.set_title("Imagem Original: Nebulosa de Órion (DSS2 Red)")
    ax1.axis('off')
    
    # Painel 2: Mapa de Magnitude dos Coeficientes de Wavelet
    ax2 = axes[1]
    im = ax2.imshow(magnitude, cmap='inferno')
    ax2.set_title(f"Transformada de Wavelet (Nível {detail_level})")
    ax2.axis('off')
    plt.colorbar(im, ax=ax2, label='Magnitude')
    
    figs = {"wavelet_orion.png": fig}
    
    resumos = {
        "objeto": "Nebulosa de Órion",
        "survey": "DSS2 Red",
        "tamanho_imagem": list(data.shape),
        "wavelet": wavelet,
        "nivel_detalhe": detail_level
    }
    
    log_str = (
        f"=== LOG DE EXECUÇÃO ===\n"
        f"Data: 2026-10-21\n"
        f"Objeto: Nebulosa de Órion\n"
        f"Survey: DSS2 Red\n"
        f"Tamanho: {data.shape}\n"
        f"Wavelet: {wavelet}, Nível de detalhe: {detail_level}\n"
        f"Objetivo: Testar se a Transformada de Wavelet detecta as estruturas de filamentos/choque conhecidas na nebulosa.\n"
    )
    
    md_str = (
        "## Teste de Controle: Wavelet na Nebulosa de Órion\n"
        "Este experimento usa uma nebulosa conhecida (Órion) para validar a ferramenta de Wavelet.\n"
        "Diferente das galáxias do SDSS (onde a esparsidade é um problema), aqui temos uma imagem contínua e densa.\n"
        "Se a Transformada de Wavelet consegue detectar as estruturas de filamentos e choques da nebulosa, isso prova que a ferramenta funciona. \n"
        "### Próximo Passo:\n"
        "Aplicar a mesma ferramenta de Wavelet no campo de densidade contínuo (KDE) das galáxias para buscar a escala de 100 Mpc."
    )
    
    salvar_kit_experimento(nome_exp, resumos, figs, log_str, md_str)
    print(f"[+] Kit completo salvo em: outputs/reports/{nome_exp}")

if __name__ == "__main__":
    main()