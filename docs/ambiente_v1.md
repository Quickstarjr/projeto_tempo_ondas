# DOCUMENTO DE AMBIENTE — PROJETO TEMPO, ONDAS E OBSERVADOR
**Data de criação:** 18 de outubro de 2026
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

### 3.1 Bibliotecas Principais
- **NumPy:** 2.5.4 (Nota: atualizado pelo JAX. PINT funciona, mas libstempo é incompatível)
- **SciPy:** 1.18.1
- **Pandas:** 3.0.6
- **Matplotlib:** 3.11.2

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
- **libstempo:** REMOVIDO (Incompatível com NumPy 2.x no WSL2)

## 4. NOTAS DE CONFIGURAÇÃO CRÍTICA
1. **GPU:** O JAX usa CUDA 12. O `nvidia-smi` confirma a GPU no WSL2.
2. **`noisedict`:** Extraído manualmente do `.par` (com espaços, ex: `EFAC 430_ASP`) porque o `enterprise` não expõe o atributo.
3. **Conversão de dados:** Arrays convertidos para `float64` antes de salvar em `.feather` (limitação do `pyarrow`).
4. **WSL2 Config:** O arquivo `C:\Users\quick\.wslconfig` limita a RAM a 12GB e desativa o timeout de ociosidade.

## 5. COMO REPRODUZIR ESTE AMBIENTE (Do zero)
```bash
conda create -n pta -c conda-forge enterprise_extensions pint-pulsar jupyterlab -y
conda activate pta
pip install -U "jax[cuda12]"
pip install discovery