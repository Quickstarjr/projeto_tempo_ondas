#!/usr/bin/env python3
import numpy as np

def build_grid(ra, dec, ra_offset, dec_offset,
               ra_cells=4, dec_cells=3):
    ra_min, ra_max = float(ra.min()), float(ra.max())
    dec_min, dec_max = float(dec.min()), float(dec.max())

    rw = (ra_max - ra_min) / ra_cells
    dw = (dec_max - dec_min) / dec_cells

    ra_origin = ra_min + ra_offset * rw
    dec_origin = dec_min + dec_offset * dw

    ra_start = int(np.floor((ra_min - ra_origin) / rw))
    ra_stop = int(np.ceil((ra_max - ra_origin) / rw))
    dec_start = int(np.floor((dec_min - dec_origin) / dw))
    dec_stop = int(np.ceil((dec_max - dec_origin) / dw))

    ra_edges = ra_origin + np.arange(ra_start, ra_stop + 1) * rw
    dec_edges = dec_origin + np.arange(dec_start, dec_stop + 1) * dw

    ri = np.searchsorted(ra_edges, ra, side="right") - 1
    di = np.searchsorted(dec_edges, dec, side="right") - 1
    ri = np.clip(ri, 0, len(ra_edges) - 2)
    di = np.clip(di, 0, len(dec_edges) - 2)

    n_ra = len(ra_edges) - 1
    n_dec = len(dec_edges) - 1
    ids = di * n_ra + ri
    counts = np.bincount(ids, minlength=n_ra * n_dec)

    assert len(ids) == len(ra)
    assert np.all(ri >= 0) and np.all(ri < n_ra)
    assert np.all(di >= 0) and np.all(di < n_dec)

    return ra_edges, dec_edges, counts

# Teste sintético: os pontos extremos e internos devem ser cobertos.
ra = np.array([140.0, 142.0, 145.0, 150.0, 155.0, 160.0])
dec = np.array([-3.0, -1.0, 2.0, 5.0, 8.0, 10.0])

for ro in [0.0, 0.25, 0.50, 0.75]:
    for do in [0.0, 0.25, 0.50, 0.75]:
        re, de, counts = build_grid(ra, dec, ro, do)
        print(
            f"RA offset={ro:.2f} DEC offset={do:.2f} | "
            f"células={len(counts)} | "
            f"largura RA={np.diff(re)} | "
            f"largura DEC={np.diff(de)} | "
            f"pontos={counts.sum()}"
        )

print("\nTESTE SINTÉTICO CONCLUÍDO")
