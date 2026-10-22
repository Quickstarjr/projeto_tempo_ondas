import json
import numpy as np
import pandas as pd

base = "outputs/reports/galaxias_tamanho/"
out = base + "auditoria_permutacao_global_grade_regular/"

with open(out + "resumo.json", encoding="utf-8") as f:
    resumo = json.load(f)

df = pd.read_csv(base + "dados.csv")
df = df[["ra", "dec", "z", "modelMag_r"]].replace(
    [np.inf, -np.inf], np.nan
).dropna()
df = df[
    df["ra"].between(0, 360)
    & df["dec"].between(-90, 90)
].copy()

df["z_bin"] = pd.cut(
    df["z"],
    bins=[0.049, 0.06, 0.07, 0.08, 0.09, 0.10],
    right=True,
    include_lowest=True,
    labels=False,
)
df = df.dropna(subset=["z_bin"]).copy()

ra = df["ra"].to_numpy(float)
dec = df["dec"].to_numpy(float)
mag = df["modelMag_r"].to_numpy(float)

best = resumo["observed_global"]
ro = best["ra_offset"]
do = best["dec_offset"]
threshold = best["threshold"]

rw = (ra.max() - ra.min()) / 4
dw = (dec.max() - dec.min()) / 3
ra_origin = ra.min() + ro * rw
dec_origin = dec.min() + do * dw

ra_start = int(np.floor((ra.min() - ra_origin) / rw))
ra_stop = int(np.ceil((ra.max() - ra_origin) / rw))
dec_start = int(np.floor((dec.min() - dec_origin) / dw))
dec_stop = int(np.ceil((dec.max() - dec_origin) / dw))

ra_edges = ra_origin + np.arange(ra_start, ra_stop + 1) * rw
dec_edges = dec_origin + np.arange(dec_start, dec_stop + 1) * dw

ri = np.clip(np.searchsorted(ra_edges, ra, side="right") - 1,
             0, len(ra_edges) - 2)
di = np.clip(np.searchsorted(dec_edges, dec, side="right") - 1,
             0, len(dec_edges) - 2)

n_ra = len(ra_edges) - 1
cell = di * n_ra + ri
counts = np.bincount(cell, minlength=n_ra * (len(dec_edges) - 1))
tail_counts = np.bincount(
    cell[mag > threshold], minlength=len(counts)
)

eligible = counts >= 100
rates = np.divide(
    tail_counts, counts,
    out=np.zeros(len(counts), dtype=float),
    where=counts > 0,
)

print("=== GRADE VENCEDORA ===")
print(f"RA offset={ro}; DEC offset={do}; limiar > {threshold}")
print(f"Amplitude registrada: {best['amplitude'] * 100:.4f} p.p.")
print(f"Total de objetos: {counts.sum()}")

print("\n=== CÉLULAS E TAXAS ===")
print("id | RA intervalo | DEC intervalo | N | cauda | taxa | elegível")
for i, n in enumerate(counts):
    if n == 0:
        continue
    ir = i % n_ra
    idec = i // n_ra
    print(
        f"{i:2d} | [{ra_edges[ir]:.3f}, {ra_edges[ir+1]:.3f}]"
        f" | [{dec_edges[idec]:.3f}, {dec_edges[idec+1]:.3f}]"
        f" | {n:4d} | {tail_counts[i]:4d}"
        f" | {rates[i]*100:7.3f}% | {bool(eligible[i])}"
    )

print("\n=== EXTREMOS ENTRE CÉLULAS ELEGÍVEIS ===")
ids = np.flatnonzero(eligible)
imin = ids[np.argmin(rates[ids])]
imax = ids[np.argmax(rates[ids])]
print(f"Mínima: célula {imin}, N={counts[imin]}, "
      f"cauda={tail_counts[imin]}, taxa={rates[imin]*100:.4f}%")
print(f"Máxima: célula {imax}, N={counts[imax]}, "
      f"cauda={tail_counts[imax]}, taxa={rates[imax]*100:.4f}%")
print(f"Amplitude recalculada: {(rates[imax]-rates[imin])*100:.4f} p.p.")
