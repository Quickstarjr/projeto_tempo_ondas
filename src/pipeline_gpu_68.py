import os
os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"
os.environ["TF_GPU_ALLOCATOR"] = "cuda_malloc_async"

import argparse
import time
import discovery as ds
import numpy as np
from enterprise.pulsar import Pulsar
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

def extrair_noisedict_do_par(par_file):
    noisedict = {}
    with open(par_file, 'r') as f:
        for line in f:
            parts = line.split()
            if not parts: continue
            key = parts[0]
            if key in ('EFAC', 'EQUAD', 'ECORR'):
                if len(parts) >= 4 and parts[1] == '-f':
                    noisedict[f'{key} {parts[2]}'] = float(parts[3])
                elif len(parts) >= 2:
                    noisedict[key] = float(parts[1])
            elif key in ('RNAMP', 'RNIDX'):
                if len(parts) >= 2:
                    noisedict[key] = float(parts[1])
    return noisedict

def processar_pulsar(args):
    """Roda em paralelo. Carrega .par/.tim, extrai ruído, salva .feather."""
    pid, par_file, tim_file = args
    try:
        ent_psr = Pulsar(par_file, tim_file)
        nd = extrair_noisedict_do_par(par_file)
        
        ent_psr._residuals = ent_psr._residuals.astype(np.float64)
        ent_psr._toas = ent_psr._toas.astype(np.float64)
        ent_psr._toaerrs = ent_psr._toaerrs.astype(np.float64)
        
        feather_file = f"{pid}.feather"
        ds.Pulsar.save_feather(ent_psr, feather_file)
        return pid, feather_file, nd, None
    except Exception as e:
        return pid, None, None, str(e)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n-pulsares', type=int, default=68)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()

    print(f"=== PIPELINE OTIMIZADO (GPU + Multiprocessing) ===")
    print(f"N pulsares: {args.n_pulsares} | Workers: {args.workers}\n")

    base_dir = Path("data/raw/nanograv_15yr/NANOGrav15yr_PulsarTiming_v2.1.0/narrowband")
    par_dir = base_dir / "par"
    tim_dir = base_dir / "tim"
    res_dir = base_dir.parent / "residuals"

    res_files = sorted(res_dir.glob("*_nb.avg.res"))
    pulsares = [f.name.split('_')[0] for f in res_files]
    if args.n_pulsares < len(pulsares):
        pulsares = pulsares[:args.n_pulsares]

    tarefas = []
    for pid in pulsares:
        par_files = list(par_dir.glob(f"{pid}_PINT_*.nb.par"))
        tim_files = list(tim_dir.glob(f"{pid}_PINT_*.nb.tim"))
        if par_files and tim_files:
            tarefas.append((pid, str(sorted(par_files)[0]), str(sorted(tim_files)[0])))

    print(f"[+] Processando {len(tarefas)} pulsares em paralelo (workers={args.workers})...")
    t0_total = time.time()
    
    # Dicionários para garantir a ordem correta, independente de quem terminar primeiro
    psrs_dict = {}
    noisedicts_dict = {}
    
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futuros = {executor.submit(processar_pulsar, t): t[0] for t in tarefas}
        
        for i, futuro in enumerate(as_completed(futuros)):
            pid, feather_file, nd, erro = futuro.result()
            if erro:
                print(f"  [{i+1}/{len(tarefas)}] {pid}: ERRO — {erro}")
            else:
                print(f"  [{i+1}/{len(tarefas)}] {pid}: OK")
                psrs_dict[pid] = ds.Pulsar.read_feather(feather_file)
                noisedicts_dict[pid] = nd

    print(f"\n[+] Carregamento concluído em {time.time()-t0_total:.1f}s")

    if len(psrs_dict) < 2:
        print("[ERRO] Menos de 2 pulsares carregados.")
        return

    # Reconstrói as listas na ordem original exata
    psrs = []
    noisedicts = {}
    for pid, _, _ in tarefas:
        if pid in psrs_dict:
            psrs.append(psrs_dict[pid])
            noisedicts[pid] = noisedicts_dict[pid]

    print(f"[+] Construindo GlobalLikelihood com {len(psrs)} pulsares...")
    t0 = time.time()
    Tspan = ds.getspan(psrs)
    
    # Como as listas estão na mesma ordem, o zip é seguro
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
            ]) for (pid, _, _), psr in zip(tarefas, psrs)
        ]
    )
    print(f"    GlobalLikelihood construído em {time.time()-t0:.1f}s")

    print("[+] Criando objeto OS...")
    os_obj = ds.OS(gbl)

    print("[+] Calculando Optimal Statistic (GPU)...")
    t0 = time.time()
    params = ds.sample_uniform(gbl.logL.params)
    
    for pid, nd in noisedicts.items():
        for key, val in nd.items():
            key_lower = key.lower().replace(' ', '_')
            if key in params: params[key] = val
            elif key_lower in params: params[key_lower] = val

    params['gw_gamma'] = 13.0 / 3.0  
    result = os_obj.os(params)
    print(f"    OS calculado em {time.time()-t0:.1f}s")

    print("\n=== RESULTADO FINAL ===")
    print(f"Pulsares: {len(psrs)}")
    print(f"SNR:      {result['snr']}")
    print(f"log10_A:  {result['log10_A']}")
    print(f"OS:       {result['os']}")
    print(f"OS_sigma: {result['os_sigma']}")

if __name__ == "__main__":
    main()