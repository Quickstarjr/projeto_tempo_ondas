import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np

print("Buscando dados da estrela KIC 757450 (uma estrela tipo-Sol)...")
# Baixa a curva de luz do Kepler
search_result = lk.search_lightcurve("KIC 757450", mission="Kepler")
lc = search_result.download()

print("Limpando os dados...")
# Remove outliers (pontos muito fora da curva)
lc_clean = lc.remove_outliers(sigma=3)

print("Plotando a curva de luz...")
fig, ax = plt.subplots(figsize=(10, 4))
lc_clean.plot(ax=ax)
ax.set_title("Curva de Luz - KIC 757450 (Variação de Brilho)")
ax.set_ylabel("Fluxo Normalizado")
plt.savefig('outputs/plots/curva_luz_estrela.png', dpi=120)
print("[+] Gráfico salvo em outputs/plots/curva_luz_estrela.png")
# Adicione no final do seu script:
print("Calculando o Periodograma (Transformada de Fourier)...")
periodograma = lc_clean.to_periodogram(method="lombscargle")

fig, ax = plt.subplots(figsize=(10, 4))
periodograma.plot(ax=ax)
ax.set_title("Periodograma - A 'Música' da KIC 757450")
ax.set_xlabel("Período (dias)")
ax.set_ylabel("Potência")
plt.savefig('outputs/plots/periodograma_estrela.png', dpi=120)
print("[+] Gráfico salvo em outputs/plots/periodograma_estrela.png")
# Remove a tendência lenta (como a rotação de 15 dias)
lc_flatten = lc_clean.flatten(window_length=21)

# Cria o periodograma apenas dos trânsitos
periodograma_transito = lc_flatten.to_periodogram(method="lombscargle")

fig, ax = plt.subplots(figsize=(10, 4))
periodograma_transito.plot(ax=ax)
ax.set_title("Periodograma Achatado - Procurando Trânsitos")
ax.set_xlabel("Período (dias)")
ax.set_ylabel("Potência")
plt.savefig('outputs/plots/periodograma_achatado_estrela.png', dpi=120)
print("[+] Gráfico salvo em outputs/plots/periodograma_achatado_estrela.png")