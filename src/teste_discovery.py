import os
os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"
os.environ["TF_GPU_ALLOCATOR"] = "cuda_malloc_async"
"""
teste_discovery.py — Teste de fumaça do optimal statistic (v11).

Correções:
  - noisedict extraído manualmente com espaços (formato enterprise).
  - noisedict injetado corretamente nos params antes do OS.
  - gw_gamma fixado em 13/3.
  - GPU (JAX) pronta para uso.
"""
import argparse
import time
import discovery as ds
import numpy as np
from enterprise.pulsar import Pulsar
from pathlib import Path


def extrair_noisedict_do_par(par_file):
    """Extrai parâmetros de ruído do arquivo .par no formato do enterprise."""
    noisedict = {}
    with open(par_file, 'r') as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            key = parts[0]
            if key in ('EFAC', 'EQUAD', 'ECORR'):
                if len(parts) >= 4 and parts[1] == '-f':
                    # O enterprise espera 'EFAC nome_do_backend' (com espaço)
                    noisedict[f'{key} {parts[2]}'] = float(parts[3])
                elif len(parts) >= 2:
                    noisedict[key] = float(parts[1])
            elif key in ('RNAMP', 'RNIDX'):
                if len(parts) >= 2:
                    noisedict[key] = float(parts[1])
    return noisedict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n-pulsares', type=int, default=5)
    args = parser.parse_args()

    print(f"=== TESTE DISCOVERY — OPTIMAL STATISTIC (v11) ===")
    print(f"N pulsares: {args.n_pulsares}\n")

    base_dir = Path("data/raw/nanograv_15yr/NANOGrav15yr_PulsarTiming_v2.1.0/narrowband")
    par_dir = base_dir / "par"
    tim_dir = base_dir / "tim"
    res_dir = base_dir.parent / "residuals"

    res_files = sorted(res_dir.glob("*_nb.avg.res"))
    pulsares = [f.name.split('_')[0] for f in res_files]
    if args.n_pulsares < len(pulsares):
        pulsares = pulsares[:args.n_pulsares]

    print(f"[+] Processando {len(pulsares)} pulsares...\n")

    psrs = []
    noisedicts = {}

    for i, pid in enumerate(pulsares):
        t0 = time.time()
        par_files = list(par_dir.glob(f"{pid}_PINT_*.nb.par"))
        tim_files = list(tim_dir.glob(f"{pid}_PINT_*.nb.tim"))
        if not par_files or not tim_files:
            print(f"  [{i+1}/{len(pulsares)}] {pid}: FALTA .par ou .tim")
            continue

        par_file = str(sorted(par_files)[0])
        tim_file = str(sorted(tim_files)[0])
        print(f"  [{i+1}/{len(pulsares)}] Carregando {pid}...", end=" ", flush=True)

        try:
            ent_psr = Pulsar(par_file, tim_file)

            # Extrai noisedict do .par manualmente
            noisedicts[pid] = extrair_noisedict_do_par(par_file)

            # Converte arrays para float64 (compatibilidade pyarrow)
            ent_psr._residuals = ent_psr._residuals.astype(np.float64)
            ent_psr._toas = ent_psr._toas.astype(np.float64)
            ent_psr._toaerrs = ent_psr._toaerrs.astype(np.float64)

            feather_file = f"{pid}.feather"
            ds.Pulsar.save_feather(ent_psr, feather_file)
            psr = ds.Pulsar.read_feather(feather_file)
            psrs.append(psr)
            
            print(f"OK ({time.time()-t0:.1f}s) — {len(noisedicts[pid])} params de ruído")
        except Exception as e:
            print(f"ERRO — {e}")
            continue

    if len(psrs) < 2:
        print(f"\n[ERRO] Apenas {len(psrs)} pulsares carregados.")
        return

    print(f"\n[+] Construindo GlobalLikelihood com {len(psrs)} pulsares...")
    t0 = time.time()
    Tspan = ds.getspan(psrs)
    gbl = ds.GlobalLikelihood(
        [
            ds.PulsarLikelihood([
                psr.residuals,
                ds.makenoise_measurement(psr, noisedict=noisedicts[pid]),
                ds.makegp_ecorr(psr, noisedict=noisedicts[pid]),
                ds.makegp_timing(psr, svd=True),
                ds.makegp_fourier(psr, ds.powerlaw, 30, T=Tspan, name='rednoise'),
                ds.makegp_fourier(psr, ds.powerlaw, 14, T=Tspan,
                                  common=['gw_log10_A', 'gw_gamma'], name='gw')
            ]) for pid, psr in zip(pulsares, psrs)
        ]
    )
    print(f"    GlobalLikelihood construído em {time.time()-t0:.1f}s")

    print("[+] Criando objeto OS...")
    t0 = time.time()
    os_obj = ds.OS(gbl)
    print(f"    OS criado em {time.time()-t0:.1f}s")

    print("[+] Calculando Optimal Statistic...")
    t0 = time.time()
    
    # Sorteia parâmetros iniciais
    params = ds.sample_uniform(gbl.logL.params)
    
    # Injeta os valores reais de ruído nos parâmetros
    for pid, nd in noisedicts.items():
        for key, val in nd.items():
            key_lower = key.lower().replace(' ', '_')
            if key in params:
                params[key] = val
            elif key_lower in params:
                params[key_lower] = val

    # Fixa o índice espectral do fundo de GW
    params['gw_gamma'] = 13.0 / 3.0  
    
    # Calcula o OS (Aqui a GPU deve entrar em ação!)
    result = os_obj.os(params)
    print(f"    OS calculado em {time.time()-t0:.1f}s")

    print("\n=== RESULTADO ===")
    print(f"Pulsares processados: {len(psrs)}")
    print(f"SNR:      {result['snr']}")
    print(f"log10_A:  {result['log10_A']}")
    print(f"OS:       {result['os']}")
    print(f"OS_sigma: {result['os_sigma']}")


if __name__ == "__main__":
    main()