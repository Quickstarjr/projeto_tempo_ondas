import os
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np

print("Baixando TODOS os quarters disponíveis para KIC 757450...")
# download_all() baixa todas as observações disponíveis
search_result = lk.search_lightcurve("KIC 757450", mission="Kepler")
lc_collection = search_result.download_all()
lc = lc_collection.stitch().remove_outliers(sigma=3)

print(f"Total de pontos após juntar tudo: {len(lc)}")
print(f"Cobertura temporal: {lc.time.value.max() - lc.time.value.min():.1f} dias")

# --- Gráfico 1: Curva de Luz Completa ---
fig1, ax1 = plt.subplots(figsize=(12, 4))
lc.plot(ax=ax1)
ax1.set_title("Curva de Luz Completa - KIC 757450")

# --- Gráfico 2: Phase Folding (O Teste Definitivo) ---
periodo_suspeito = 18.80
folded_lc = lc.fold(period=periodo_suspeito)

fig2, ax2 = plt.subplots(figsize=(8, 5))
folded_lc.scatter(ax=ax2, s=1, alpha=0.5)
ax2.set_title(f"Curva Dobrada (Phase Folded) - Período: {periodo_suspeito} dias")
ax2.set_xlabel("Fase")
ax2.set_ylabel("Fluxo Normalizado")

# Salvar os gráficos
os.makedirs("outputs/plots", exist_ok=True)
fig1.savefig("outputs/plots/estrela_completa.png", dpi=120)
fig2.savefig("outputs/plots/estrela_folded.png", dpi=120)

print("[+] Gráficos salvos em outputs/plots/")
print("[+] Se houver um 'poço' (dip) claro no centro do gráfico dobrado, é um forte candidato a trânsito.")