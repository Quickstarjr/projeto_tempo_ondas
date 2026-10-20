# DOCUMENTO DE AMBIENTE — PROJETO TEMPO, ONDAS E OBSERVADOR
**Versão:** 2.0
**Data de atualização:** 20 de outubro de 2026
**Máquina:** SSW1 (Desktop)
**Ambiente de Execução:** WSL2 (Windows Subsystem for Linux)

## 1. HARDWARE (HOST WINDOWS)
- **Processador:** Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz
- **Memória RAM:** 16.0 GB (sendo 11 GiB alocados dinamicamente para o WSL2)
- **Armazenamento:** HDD WDC WD5000AZLX (466 GB)
- **Placa de Vídeo:** NVIDIA GeForce GTX 1050 Ti (4 GB VRAM) — Driver 582.28
- **Sistema Operacional:** Windows 10 (Build 19045.6466)

## 2. SISTEMA OPERACIONAL (WSL2)
- **WSL:** Versão 2
- **Distribuição:** Ubuntu 26.04.1 LTS (Codename: resolute)
- **Kernel Linux:** 6.18.54.1-microsoft-standard-WSL2

## 3. AMBIENTE PYTHON (Conda: `pta`)
- **Python:** 3.13.16
- **Conda:** 26.7.2

### 3.1 Bibliotecas Principais e de Astronomia Geral
- **NumPy:** 2.5.4 (Nota: atualizado pelo JAX. PINT funciona, mas libstempo é incompatível)
- **SciPy:** 1.18.1
- **Pandas:** 3.0.6
- **Matplotlib:** 3.11.2
- **Astropy:** (Versão mais recente do conda-forge) — Usada para cálculos cosmológicos e coordenadas.
- **Astroquery:** (Versão mais recente do conda-forge) — Usada para baixar dados do SDSS.
- **Lightkurve:** (Versão mais recente do conda-forge) — Usada para análise de curvas de luz (Kepler/TESS).

### 3.2 Aceleração por Hardware (GPU)
- **JAX:** 0.11.2
- **JAXlib:** 0.11.2
- **Plugins CUDA:** jax-cuda12-pjrt 0.11.2, jax-cuda12-plugin 0.11.2
- **Status:** GPU validada e pronta para uso (`[CudaDevice(id=0)]`).

### 3.3 Bibliotecas de Astrofísica de Pulsares (NANOGrav)
- **PINT:** 1.1.8 (Motor de timing oficial, rodando com precisão nativa no Linux)
- **PyArrow:** 25.0.0
- **Discovery:** 0.5 (Framework oficial NANOGrav para Optimal Statistic)
- **Enterprise_extensions:** 3.0.3
- **Enterprise-pulsar:** 0.0.0 (Dev build)
- **MPI (Batalha do MCMC):** `mpi4py` (4.1.2), `mpi4jax` (0.11.2) e `openmpi` instalados, mas contornados com JAX_PLATFORMS="cpu" devido a conflitos.

## 4. NOTAS DE CONFIGURAÇÃO CRÍTICA
1. **GPU:** O JAX usa CUDA 12. O `nvidia-smi` confirma a GPU no WSL2.
2. **`noisedict`:** Extraído manualmente do `.par` (com espaços, ex: `EFAC 430_ASP`) porque o `enterprise` não expõe o atributo.
3. **Conversão de dados:** Arrays convertidos para `float64` antes de salvar em `.feather` (limitação do `pyarrow`).
4. **WSL2 Config:** O arquivo `C:\Users\quick\.wslconfig` limita a RAM a 12GB e desativa o timeout de ociosidade.
5. **Filtro SDSS (SpecPhoto):** Ao baixar galáxias, usar a tabela `SpecPhoto` e adicionar `AND modelMag_r > 0` no SQL para evitar dados ausentes (`-9999.0`).
6. **Limitação do MCMC:** O `PTMCMCSampler` exige conversão manual de arrays para dicionários no `discovery`. A taxa de aceitação é 0% na CPU local para 2 pulsares.

## 5. COMO REPRODUZIR ESTE AMBIENTE (Do zero)
```bash
# 1. Criar ambiente base
conda create -n pta -c conda-forge enterprise_extensions pint-pulsar jupyterlab -y
conda activate pta

# 2. Instalar aceleração GPU (JAX)
pip install -U "jax[cuda12]"

# 3. Instalar framework NANOGrav
pip install discovery

# 4. Instalar bibliotecas de análise estelar e galáctica
conda install -c conda-forge astroquery astropy lightkurve -y

# 5. Instalar dependências MPI (opcional, para MCMC)
conda install -c conda-forge mpi4py mpi4jax openmpi -y