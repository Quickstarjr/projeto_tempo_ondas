# REGISTRO DE RESULTADOS E EVOLUÇÃO DO PIPELINE
**Projeto:** Investigação sobre Tempo, Ondas e Observador
**Versão do Documento:** 2.0 (Atualizado com Optimal Statistic)
**Data:** 18 de outubro de 2026
**Autores:** Quickstar + Gepeto + Grokinha + Gemini + Deep (DeepSeek)
**Pré-registro congelado:** commit `cb4558b`

---

# PARTE 1: ANÁLISE SIMPLIFICADA INICIAL (DADOS REAIS)
**Pipeline utilizado:** `src/pipeline_real.py`

## 1. O QUE FOI OBSERVADO INICIALMENTE
Análise em dados reais do NANOGrav 15yr (release v2.1.0):
- 68 pulsares
- 2.274 pares com overlap temporal suficiente (>=10 bins)
- Correlação média global: **+0.0019**
- Desvio padrão: **0.1972**
- Bins angulares: sem estrutura evidente (todos ~0 ± erro)
- χ² observado: **145.53**
- p-valor (sky scramble, 100 iterações): **0.430**

**Resultado:** Nenhuma anisotropia estatisticamente significativa detectada por esta implementação simplificada.

## 2. INTERPRETAÇÃO E LIÇÕES
### O que o resultado SIGNIFICA
- O pipeline processa dados reais corretamente.
- O teste nulo (sky scramble) funciona: p = 0.430 é o esperado quando não há sinal.
- O pré-registro foi respeitado: todos os bins foram reportados.

### O que o resultado NÃO significa
- **NÃO significa** que não há anisotropia nos dados do NANOGrav. Significa que esta análise simplificada não tem sensibilidade para detectá-la.
- **NÃO significa** que a HD está ausente. A HD já foi detectada pelo NANOGrav com metodologia adequada (optimal statistic). Nosso pipeline simplificado não a recupera porque não usa essa metodologia.

### Frase-chave (Gepeto)
> "Não devemos transformar 'não detectamos' em 'não existe'."

### Por que o resultado nulo era esperado
1. **Red noise intrínseco não modelado.** Cada pulsar tem ruído vermelho próprio que domina a variância em baixas frequências.
2. **Sem optimal statistic.** A literatura PTA usa o optimal statistic (Chamberlin et al. 2015), que pondera por erros individuais.
3. **Sem correção de Shklovskii nem aceleração galáctica.**
4. **Reamostragem mensal** introduz correlação artificial dentro do mesmo bin.

A literatura de 2024-2026 (Fang et al., 2026) já reporta nulo em teste equivalente de anisotropia correlacionada com LSS. Nosso resultado é **consistente com a literatura**.

---

# PARTE 2: VALIDAÇÃO DO MÉTODO E LIMIAR DE SENSIBILIDADE
**Pipeline utilizado:** `src/pipeline_hd.py` (Dados sintéticos com injeção de HD)

## 3. FRAMEWORK DE TESTES (Proposta Gepeto)
Adotamos o framework de 4 camadas para evitar falsos positivos:
- **TESTE 1:** Pipeline + ruído → *não inventa sinal* ✅
- **TESTE 2:** Pipeline + sinal HD conhecido injetado → *recupera sinal conhecido* ✅
- **TESTE 3:** Dados reais + modelo convencional → *procura resíduos/anomalias* ✅ (nulo)
- **TESTE 4:** Hipótese Grande Onda → *procura assinatura específica* ⏳ (Desbloqueado com OS)

## 4. TESTE 2 — RECUPERAÇÃO DE HD E SCANS
### 4.1 Teste único (amplitude 5.0, sem red noise)
- r = 0.982, p = 0.000 → pipeline RECUPERA HD ✅
- Bins reproduzem a estrutura em U da HD.

### 4.2 Scan sem Red Noise (1 seed)
- Limiar de detecção inicial: SNR ≈ 0.5 - 1.0.
- *Anomalia residual em SNR=0.1:* r = -0.84 (falso positivo em SNR baixo). Isso demonstrou empiricamente por que o **sky scramble é obrigatório**.

### 4.3 Scan com Múltiplas Seeds (Robustez)
Configuração: 5 seeds por amplitude, ruído vermelho = 0.0.
Resultado:
- **SNR < 0.2:** Detecção nula (0/5). Regime de ruído puro.
- **0.3 < SNR < 0.6:** Detecção intermitente (2/5 a 3/5). Zona de transição difusa.
- **SNR >= 1.0:** Detecção robusta (5/5). r médio > 0.89. Recuperação determinística.

**LIMIAR CONFIRMADO:** SNR >= 1.0 para detecção robusta; SNR < 0.3 para não-detecção.

### 4.4 Scan com Red Noise Realista = 1.0
- Limiar de detecção: SNR ≈ 1.0.
- Comportamento limpo, sem falsos positivos.

**CONCLUSÃO DA PARTE 2:** O pipeline recupera HD em simulação quando SNR ≥ 1. Dados reais deram r ≈ 0 no pipeline simplificado → SNR efetivo < 1 (consistente com a falta de modelagem de red noise).

---

# PARTE 3: A VIRADA — OPTIMAL STATISTIC OFICIAL (DISCOVERY)
**Pipeline utilizado:** `src/teste_discovery.py` / `src/pipeline_gpu_68.py`

## 5. MIGRAÇÃO E EVOLUÇÃO TÉCNICA
Para aumentar o SNR efetivo e desbloquear o Teste 4, abandonamos o pipeline simplificado em Python puro e passamos a usar o **`discovery`**, a biblioteca oficial do NANOGrav baseada em JAX.
- **Ambiente:** WSL2 (Ubuntu) com 12 GB de RAM.
- **Hardware:** Aceleração por GPU (NVIDIA GTX 1050 Ti) via CUDA 12.
- **Tratamento de ruído:** Extração manual do `noisedict` do arquivo `.par` e injeção via matriz de covariância.

## 6. RESULTADO PRELIMINAR (5 PULSARES)
O primeiro teste bem-sucedido com a modelagem correta de ruído (noisedict com espaçamento `EFAC backend`) e `gw_gamma` fixado em 13/3:

- **Pulsares processados:** 5
- **SNR:** **+1.366** (Positivo ✅)
- **log10_A:** -14.495
- **OS:** 3.09 × 10⁻²⁹
- **OS_sigma:** 2.26 × 10⁻²⁹

### Interpretação
O SNR positivo confirma que o pipeline matemático está correto. O valor (1.36) é excelente para apenas 5 pulsares (10 pares). O sinal real emergirá com mais força quando rodarmos os 68 pulsares, mas a barreira técnica foi vencida.

---

## 7. REGRA METODOLÓGICA REAFIRMADA
**Se o resultado for nulo, publicamos nulo.**
**Se for estranho, primeiro tentamos destruir o resultado antes de tentar explicá-lo pela Grande Onda.**

## 8. OBSERVAÇÃO DA GEMINI
> "Se tivesse aparecido uma curva HD 'bonita' no gráfico sem esse tratamento, seria um falso positivo decorrente de contaminação cinemática ou bug. O pré-registro nos salvou de um confirmation bias!"

---

## 9. REFERÊNCIAS
- Chamberlin, S. J., et al. (2015). "Time-domain implementation of the pulsar timing array optimal statistic." ApJ 810, 74.
- Fang et al. (2026). "A Template-Based Search for Large-Scale-Structure-Correlated Anisotropy in the Nanohertz Gravitational-Wave Background." arXiv.
- NANOGrav Collaboration (2023). 15yr Data Set.
- Documento de Ambiente: `docs/ambiente_v1.md`.
---

# PARTE 4: TESTE DE ESCALA COM 20 PULSARES E LIMITAÇÕES DE HARDWARE
**Data:** 18 de outubro de 2026
**Pipeline utilizado:** `src/pipeline_gpu_68.py`

## 10. O RESULTADO E A ARMADILHA DO FALSO POSITIVO
Após resolvermos os gargalos de memória e rodarmos a paralelização, o teste com 20 pulsares terminou com sucesso. No entanto, o resultado acendeu um alerta vermelho imediato:

- **SNR:** **41.31** (Astronomicamente alto)
- **log10_A:** -16.38
- **Tempo de cálculo:** 70s (na CPU)

### Análise Crítica (A Regra de Ouro do Gepeto)
Um SNR de 41 está muito acima do esperado. A detecção oficial do NANOGrav 15yr com 68 pulsares tem um SNR entre 3 e 5. Nós "detectamos" um sinal 10 vezes maior com apenas 20 pulsares. **Isso é um falso positivo.**

**Por que isso aconteceu?**
1. O `discovery` foi alimentado com os parâmetros de ruído (`noisedict`) exatos extraídos do `.par`.
2. O `gw_gamma` foi fixado em 13/3.
3. Não foi aplicada a **marginalização via MCMC**.
O modelo de covariância ficou "rígido" demais. Qualquer mínima correlação residual entre os pulsares foi interpretada pela matemática como um sinal de ondas gravitacionais monstruoso. Na literatura real, o `OS` varia os parâmetros de ruído via amostragem para calcular a incerteza correta.

## 11. LIMITAÇÕES DE HARDWARE (A Realidade Nua e Crua)
Documentamos aqui as limitações físicas da máquina utilizada (SSW1), que afetam diretamente o escopo do projeto:
- **Processador:** Intel i7-2600 (4 núcleos, lançado em 2011).
- **Memória RAM:** 16 GB (12-14 GB alocados para o WSL2). O `free -h` mostrou que rodar o PINT com 4 workers estourou a memória e o swap.
- **Armazenamento:** HDD Mecânico (o gargalo real, com tempos de I/O lentos).
- **GPU:** NVIDIA GTX 1050 Ti (4 GB VRAM). Insuficiente para o `GlobalLikelihood` de 20+ pulsares, sofrendo *Out of Memory*.

**Conclusão de Hardware:** A máquina é um feito de resistência, mas não suporta a carga de processamento (MCMC) necessária para os 68 pulsares. Precisamos definir os próximos passos considerando essa limitação.
---

# PARTE 5: PAUSA NA ANÁLISE DE DADOS E LIMITAÇÕES DE INFRAESTRUTURA
**Data:** 19 de outubro de 2026

## 12. TENTATIVA DE USO DO GOOGLE COLAB E FALHA POR MEMÓRIA
Após o falso positivo de SNR=41.31 (20 pulsares, parâmetros de ruído fixos), o grupo tentou migrar a análise para o Google Colab (GPU Tesla T4, 12.7 GB RAM) para rodar a marginalização MCMC.

**Resultado:** A sessão do Colab falhou repetidamente por *Out of Memory* (OOM) ao tentar carregar 5 pulsares e construir o `GlobalLikelihood`. O limite de 12.7 GB de RAM do plano gratuito é insuficiente para o `discovery`/JAX.

**Conclusão:** A máquina local (WSL2, 14 GB RAM + 16 GB swap) é mais resiliente para o MCMC do que o Colab gratuito, mas ainda assim não suporta a escala de 68 pulsares.

## 13. DECISÃO DO GRUPO
- **Curto prazo:** Pausar a análise de dados em larga escala. O foco será a documentação metodológica e a teoria.
- **Médio prazo:** Explorar o MCMC local com 2 pulsares para provar o conceito (que a marginalização derruba o SNR inflado).
- **Longo prazo:** Buscar infraestrutura adequada (cluster, nuvem paga) ou reduzir o escopo para uma prova de conceito com poucos pulsares.

## 14. PRÓXIMOS TESTES SUGERIDOS (PENDENTES)
- **MCMC Local (2 pulsares):** Rodar o script `pipeline_mcmc_local.py` na CPU local para verificar se o SNR cai de valores inflados para a faixa 0.5–3.0.
- **Reanálise com mais bins angulares:** A análise simplificada inicial usou 10 bins. O Gepeto sugeriu aumentar para 20 bins (ou mais) para melhorar a resolução da curva de correlação vs θ. Isso pode revelar estrutura que os 10 bins suavizaram.
- **Documentação da "Crônica da Falha do Colab":** Registrar no `Gemini.md` e no `CHANGELOG.md` que o Colab gratuito não é viável para este pipeline, como lição de infraestrutura.
============================================================
FIM DO REGISTRO
============================================================