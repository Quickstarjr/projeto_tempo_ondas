import os
os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"
os.environ["JAX_PLATFORMS"] = "cpu" 

import numpy as np
from pathlib import Path
import discovery as ds
from PTMCMCSampler.PTMCMCSampler import PTSampler

N_PULSARES = 2
N_ITER = 1000

print(f"=== [1/5] CARREGANDO {N_PULSARES} PULSARES (FEATHER) ===")
feather_files = sorted(list(Path('.').glob('*.feather')))[:N_PULSARES]
psrs = [ds.Pulsar.read_feather(str(f)) for f in feather_files]
print(f"[+] Carregados: {[f.name for f in feather_files]}")

print("\n=== [2/5] CONSTRUINDO GLOBAL LIKELIHOOD (SEM NOISEDICT FIXO) ===")
Tspan = ds.getspan(psrs)

gbl = ds.GlobalLikelihood(
    [
        ds.PulsarLikelihood([
            psr.residuals,
            ds.makenoise_measurement(psr), 
            ds.makegp_ecorr(psr),
            ds.makegp_timing(psr, svd=True),
            ds.makegp_fourier(psr, ds.powerlaw, 30, T=Tspan, name='rednoise'),
            ds.makegp_fourier(psr, ds.powerlaw, 14, T=Tspan,
                              common=['gw_log10_A', 'gw_gamma'], name='gw')
        ]) for psr in psrs
    ]
)

print("\n=== [3/5] CONFIGURANDO O MCMC (SEM MPI) ===")
# Extrai os parâmetros como dicionário
p0_dict = ds.sample_uniform(gbl.logL.params)
p0 = np.array(list(p0_dict.values()))
keys = list(p0_dict.keys())
ndim = len(p0)

cov = np.diag(np.ones(ndim) * 0.1)
outDir = 'mcmc_chains'
os.makedirs(outDir, exist_ok=True)

# A PONTE: Converte array (do sampler) para dicionário (do discovery)
# Usa logL (sem MPI) e prior uniforme (0.0)
logl_func = gbl.logL
def logl(x):
    params = dict(zip(keys, x))
    return logl_func(params)

def logp(x):
    # Prior uniforme: todos os valores são igualmente prováveis.
    # Para um teste de conceito, isso é aceitável.
    return 0.0

sampler = PTSampler(
    ndim=ndim,
    logl=logl,
    logp=logp, 
    cov=cov,
    outDir=outDir
)

print(f"\n=== [4/5] RODANDO MCMC COM {N_ITER} ITERAÇÕES NA CPU ===")
print("(Isso vai demorar. Acompanhe com tail -f)")
sampler.sample(p0, N_ITER)

print("\n=== [5/5] CALCULANDO OPTIMAL STATISTIC MARGINALIZADO ===")
os_obj = ds.OS(gbl)
# O chain_os precisa das chaves dos parâmetros para ler a cadeia
result = os_obj.chain_os(outDir, N_ITER, params=keys)

print("\n====================================================")
print("     RESULTADO MARGINALIZADO (MCMC LOCAL)          ")
print("====================================================")
print(f"Pulsares processados: {len(psrs)}")
print(f"SNR:      {result.get('snr')}")
print(f"log10_A:  {result.get('log10_A')}")
print(f"OS:       {result.get('os')}")
print(f"OS_sigma: {result.get('os_sigma')}")
print("====================================================")