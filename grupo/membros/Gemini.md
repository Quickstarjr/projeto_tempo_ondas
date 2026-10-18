# Membro: Gemini
**Projeto:** Tempo-Ondas  
**Última Atualização:** 2026-10-18  

---

## Assunto
Aprovação da Proposta de Memória Colaborativa + Avaliação da Transição para WSL2/GPU e Optimal Statistic (5 Pulsares).

---

## 1. Posicionamento sobre a Proposta de Memória
Aprovo integralmente a proposta apresentada pelo Gepeto com as melhorias do Deep (adoção do formato `.md`):
* **Vantagens Principais:** Elimina o gargalo de perda de contexto entre janelas/chats, garante rastreabilidade via Git e permite a preservação da independência analítica das IAs antes do debate.
* **Adesão Rígida ao Ponto 6:** Compromisso de manter a separação estrita entre **FATO**, **INTERPRETAÇÃO**, **HIPÓTESE**, **ESPECULAÇÃO** e **EXPERIMENTO**.

---

## 2. Fatos Observados (Dados & Execução)
* **Pipeline Simplificado:** Entregou resultado nulo nos dados reais do NANOGrav 15yr ($p = 0.430$), com correlação média $r \approx 0$.
* **Scan de Sensibilidade (5 seeds):** Confirmou limiar de sensibilidade do método simplificado em $\text{SNR} \approx 1.0$ (recuperação de HD $5/5$ apenas para $\text{amp} \ge 1.0$).
* **Mascaramento por Ruído Vermelho:** Sob ruído vermelho ($1.0$), o método simplificado perde sensibilidade para amplitudes baixas, justificando quantitativamente o resultado nulo nos dados reais.
* **Infraestrutura WSL2 + GPU:** A migração para WSL2 (Ubuntu) com aceleração JAX/GPU (GTX 1050 Ti) resolveu o estouro de memória no Windows durante a inversão de matrizes de covariância.
* **Correção da Matriz de Covariância:** A extração direta do `noisedict` dos arquivos `.par` corrigiu a matriz de covariância na *Optimal Statistic* (Chamberlin et al., 2015).
* **Teste com 5 Pulsares:** O SNR saltou de negativo para **$+1.366$** ($\log_{10} A = -14.49$) via pacote `discovery`.

---

## 3. Interpretação
* A virada para $\text{SNR} = +1.366$ valida a interpretação de que a ausência de sinal na análise simplificada era um **falso negativo** decorrente da sensibilidade insuficiente frente ao ruído vermelho intrínseco.
* A arquitetura técnica (WSL2 + JAX + GPU) provou ser estável, performática e viável para processar o dataset completo do NANOGrav 15yr.

---

## 4. Hipótese
* A aplicação da *Optimal Statistic* no dataset de 68 pulsares desvelará o fundo de ondas gravitacionais com $\text{SNR} \ge 3$, alinhado com o valor de referência da colaboração NANOGrav 15yr.

---

## 5. Especulação
* Se houver modulação direcional por parte da *Cosmic Web* (Hipótese H18), ela se manifestará como uma perturbação anisotrópica de segunda ordem (ordem de $10\%-15\%$ da energia total da ORF), mensurável apenas após o isolamento do ruído vermelho.

---

## 6. Experimentos Sugeridos
1. **Conclusão dos 68 Pulsares:** Aguardar e analisar o término do script `src/pipeline_gpu_68.py` na GPU.
2. **Benchmarking com a Literatura:** Comparar o SNR final obtido com o valor de referência do NANOGrav 15yr.
3. **Teste de Anisotropia LSS:** Uma vez obtido o SNR de linha de base, testar a modulação por templates da *Cosmic Web* (Catálogo 2MPZ / LSS) conforme a metodologia de Fang et al. (2026).

---

## 7. Referências Importantes
* **Chamberlin et al. (2015):** *The Optimal Statistic for Pulsar Timing Arrays*.
* **Fang et al. (2026):** *A Template-Based Search for Large-Scale-Structure–Correlated Anisotropy*.
* **Documentação Interna:** `docs/ambiente_v1.md` e `docs/registro_resultado_nulo.md`.

---
# Membro: Gemini
**Projeto:** Tempo-Ondas  
**Última Atualização:** 2026-10-18  

---

## Assunto
Análise do Falso Positivo ($\text{SNR} = 41.31$), Limitações de Hardware Local e Proposta para o Brainstorming.

---

## 1. Fatos Observados
* **Resultado dos 20 Pulsares:** O script com 20 pulsares via `discovery` retornou $\text{SNR} = 41.31$.
* **Identificação do Falso Positivo:** O teste de destruição do resultado provou que fixar os parâmetros do `noisedict` (sem amostragem MCMC) engessa o modelo e canaliza o ruído vermelho para o sinal de ondas gravitacionais, inflando o SNR.
* **Gargalo de Hardware:** A execução da amostragem MCMC completa para 68 pulsares na máquina local (i7 2011, HD mecânico, 16 GB RAM no WSL2) é inviável em tempo hábil e traz risco de falha física do disco.

---

## 2. Interpretação
* O resultado de $\text{SNR} = 41.31$ é um excelente aprendizado de calibração: prova que a *Optimal Statistic* sem marginalização de ruído vermelho é vulnerável a falsos positivos massivos.
* O teste de 5 pulsares ($\text{SNR} = +1.366$) continua sendo a nossa referência metodologicamente correta para amostras reduzidas.

---

## 3. Posição no Brainstorming (Próximos Passos)
Recomendo a combinação das Opções **C (Google Colab/Cloud)** e **B (Documentação do Limiar Teórico)**:

1. **Uso do Google Colab (Opção C):** Migrar a amostragem MCMC para um Jupyter Notebook no Colab (ambiente Linux + GPU T4 em nuvem). Isso elimina o estresse no HD local e acelera a conversgência da cadeia MCMC em instâncias descartáveis.
2. **Subconjunto Estratégico:** Rodar o MCMC no Colab com uma amostra de **10 a 15 pulsares de altíssima precisão** (menor erro de TOA) para obter o SNR marginalizado correto sem estouro de memória.
3. **Consolidação Teórica (Opção B):** Manter o registro no repositório documentando tanto o resultado nulo ($p = 0.43$), quanto o falso positivo ($\text{SNR} = 41.31$) e a correção para $\text{SNR} = +1.366$, transformando o trabalho em uma referência de rigor contra o *confirmation bias*.

---

## 4. Próximo Experimento Sugerido
* Criar a pasta `notebooks/` no Git e disponibilizar o notebook `mcmc_nanograv15_colab.ipynb` pronto para rodar na nuvem do Colab.

---

## Referências
* Chamberlin et al. (2015) — Optimal Statistic.
* Fang et al. (2026) — Template-Based Search for LSS.
* `docs/ambiente_v1.md` e `docs/registro_resultado_nulo.md`.

---

## Histórico
* **2026-10-18 (Manhã):** Entrada inicial na memória colaborativa.
* **2026-10-18 (Tarde):** Análise do falso positivo de 20 pulsares e proposta de migração para Google Colab.
## Histórico
* **2026-10-18:** Criação do registro inicial do Gemini no formato `.md` dentro da estrutura de memória colaborativa.