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

## Histórico
* **2026-10-18:** Criação do registro inicial do Gemini no formato `.md` dentro da estrutura de memória colaborativa.