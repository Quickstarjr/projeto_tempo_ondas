import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform

def gerar_dados_sinteticos_pta(n_pulsares=50, n_observacoes=100):
    """
    Gera um conjunto de dados sintético imitando os resíduos de tempo (Timing Residuals)
    de Pulsar Timing Arrays (PTAs) com coordenadas celestes (RA, DEC).
    Útil para testar o pipeline localmente antes de baixar os arquivos de múltiplos GB do Zenodo/NANOGrav.
    """
    np.random.seed(42)
    
    # Coordenadas celestes (Ascensão Reta em graus, Declinação em graus)
    ra = np.random.uniform(0, 360, n_pulsares)
    dec = np.random.uniform(-90, 90, n_pulsares)
    
    # Tempos de observação (MJD - Modified Julian Date)
    mjd = np.linspace(53000, 59000, n_observacoes)
    
    dados = []
    for i in range(n_pulsares):
        # Simula resíduo em microssegundos (us) com ruído branco
        ruido = np.random.normal(0, 0.5, n_observacoes)
        
        # Opcional: Injeta uma oscilação de baixa frequência (simulando Hipótese 18 / Leitura 2)
        sinal_hipotetico = 0.2 * np.sin(2 * np.pi * mjd / 365.25 / 10) # ciclo de ~10 anos
        
        residuos = ruido + sinal_hipotetico
        
        for t_idx, t in enumerate(mjd):
            dados.append({
                'pulsar_id': f'J{i:02d}',
                'ra_deg': ra[i],
                'dec_deg': dec[i],
                'mjd': t,
                'residual_us': residuos[t_idx],
                'erro_us': np.random.uniform(0.05, 0.15)
            })
            
    return pd.DataFrame(dados)

def calcular_separacao_angular(ra1, dec1, ra2, dec2):
    """
    Calcula a separação angular theta (em radianos) entre dois pontos no céu
    usando a fórmula da grande-círculo (Haversine/Produto escalar).
    """
    ra1_rad, dec1_rad = np.radians(ra1), np.radians(dec1)
    ra2_rad, dec2_rad = np.radians(ra2), np.radians(dec2)
    
    cos_theta = (np.sin(dec1_rad) * np.sin(dec2_rad) + 
                 np.cos(dec1_rad) * np.cos(dec2_rad) * np.cos(ra1_rad - ra2_rad))
    
    # Garante estabilidade numérica no intervalo [-1, 1]
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    return np.arccos(cos_theta)

def extrair_matriz_correlacao_espacial(df_pta):
    """
    Agrupa resíduos por pulsar e calcula a matriz de correlação cruzada entre os resíduos
    de todos os pares de pulsares, associando à separação angular entre eles.
    """
    # Pivotar dataframe para ter linhas = MJD e colunas = pulsares
    pivot_df = df_pta.pivot(index='mjd', columns='pulsar_id', values='residual_us')
    
    # Calcular matriz de correlação de Pearson entre resíduos dos pulsares
    matriz_corr = pivot_df.corr()
    
    # Obter coordenadas únicas de cada pulsar
    coords = df_pta[['pulsar_id', 'ra_deg', 'dec_deg']].drop_duplicates().set_index('pulsar_id')
    
    pulsares = matriz_corr.columns.tolist()
    n_pulsares = len(pulsares)
    
    pares_dados = []
    
    for i in range(n_pulsares):
        for j in range(i + 1, n_pulsares):
            p1, p2 = pulsares[i], pulsares[j]
            
            ra1, dec1 = coords.loc[p1, 'ra_deg'], coords.loc[p1, 'dec_deg']
            ra2, dec2 = coords.loc[p2, 'ra_deg'], coords.loc[p2, 'dec_deg']
            
            theta_rad = calcular_separacao_angular(ra1, dec1, ra2, dec2)
            corr_val = matriz_corr.loc[p1, p2]
            
            pares_dados.append({
                'pulsar_1': p1,
                'pulsar_2': p2,
                'theta_deg': np.degrees(theta_rad),
                'correlacao_residuos': corr_val
            })
            
    return pd.DataFrame(pares_dados)

if __name__ == "__main__":
    print("=== INICIANDO PIPELINE DE PROCESSAMENTO DE DADOS PTA ===")
    
    # 1. Carregar/Gerar dados
    df_residuos = gerar_dados_sinteticos_pta(n_pulsares=30, n_observacoes=120)
    print(f"[+] Total de observações processadas: {len(df_residuos)}")
    
    # 2. Exportar Dataset de Resíduos limpo para o Pipeline
    arquivo_csv = "residuos_pta_processados.csv"
    df_residuos.to_csv(arquivo_csv, index=False)
    print(f"[+] Resíduos limpos salvos em: {arquivo_csv}")
    
    # 3. Calcular Correlação Espacial Angular (Preparo para H17/H18)
    df_pares = extrair_matriz_correlacao_espacial(df_residuos)
    
    arquivo_pares = "correlacao_pares_pta.csv"
    df_pares.to_csv(arquivo_pares, index=False)
    print(f"[+] Matriz de correlação de pares salva em: {arquivo_pares}")
    
    print("\n--- Amostra dos pares calculados ---")
    print(df_pares.head())
    print("\nPipeline concluído com sucesso!")