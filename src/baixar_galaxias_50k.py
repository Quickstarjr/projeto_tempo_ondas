import os
import pandas as pd
from astroquery.sdss import SDSS

def main():
    print("=== BAIXANDO AMOSTRA MASSIVA DO SDSS (50.000 Galáxias) ===")
    
    # Vamos expandir a área do céu (RA 130 a 180, DEC -10 a +20) e pedir mais galáxias
    query = """
    SELECT TOP 50000 
      ra, dec, z, modelMag_r
    FROM SpecPhoto 
    WHERE z BETWEEN 0.05 AND 0.1 
      AND zWarning = 0 
      AND class = 'GALAXY'
      AND ra BETWEEN 130 AND 180 
      AND dec BETWEEN -10 AND 20
      AND modelMag_r > 0
    """
    
    try:
        print("[+] Consultando SDSS (isso pode demorar um pouco)...")
        res = SDSS.query_sql(query)
        df = res.to_pandas()
    except Exception as e:
        print(f"[ERRO] Falha ao baixar: {e}")
        return
        
    print(f"[+] Galáxias obtidas: {len(df)}")
    
    # Salvar no novo caminho
    pasta = "data/processed"
    os.makedirs(pasta, exist_ok=True)
    caminho_saida = os.path.join(pasta, "galaxias_50k.csv")
    df.to_csv(caminho_saida, index=False)
    print(f"[+] Dados salvos em: {caminho_saida}")

if __name__ == "__main__":
    main()