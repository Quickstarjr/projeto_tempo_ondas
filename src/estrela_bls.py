import lightkurve as lk
import matplotlib.pyplot as plt

print("Baixando dados...")
search_result = lk.search_lightcurve("KIC 757450", mission="Kepler")
lc = search_result.download()
lc_clean = lc.remove_outliers(sigma=3)

print("Rodando o método BLS (Box Least Squares) para buscar trânsitos...")
# O BLS procura por "caixas" (dips)
periodograma_bls = lc_clean.to_periodogram(method="bls", period=np.arange(1, 20, 0.01))

fig, ax = plt.subplots(figsize=(10, 4))
periodograma_bls.plot(ax=ax)
ax.set_title("Periodograma BLS - O Verdadeiro Detector de Trânsitos")
ax.set_xlabel("Período (dias)")
ax.set_ylabel("Potência")
plt.savefig('outputs/plots/periodograma_bls_estrela.png', dpi=120)
print("[+] Gráfico salvo em outputs/plots/periodograma_bls_estrela.png")