# REGISTRO — RESULTADO NULO EM DADOS REAIS (NANOGrav 15yr)

**Data:** 16 de outubro de 2026
**Pipeline:** `src/pipeline_real.py`
**Pré-registro:** commit `cb4558b`
**Autores:** Quickstar + Gepeto + Grokinha + Gemini + Deep (DeepSeek)

---

## 1. O QUE FOI OBSERVADO

Análise em dados reais do NANOGrav 15yr (release v2.1.0):

- 68 pulsares
- 2.274 pares com overlap temporal suficiente (>=10 bins)
- 4 pares descartados por falta de overlap
- Correlação média global: **+0.0019**
- Desvio padrão: **0.1972**
- Bins angulares: sem estrutura evidente (todos ~0 ± erro)
- χ² observado: **145.53**
- p-valor (sky scramble, 100 iterações): **0.430**

**Resultado:** Nenhuma anisotropia estatisticamente significativa
detectada por esta implementação.

---

## 2. INTERPRETAÇÃO

### O que o resultado SIGNIFICA
- O pipeline processa dados reais corretamente.
- O teste nulo (sky scramble) funciona: p = 0.430 é o esperado
  quando não há sinal.
- O pré-registro foi respeitado: todos os bins foram reportados,
  inclusive os nulos.
- A ausência de HD aparente é consistente com o esperado para
  uma análise simplificada que NÃO modela red noise.

### O que o resultado NÃO significa
- **NÃO significa** que não há anisotropia nos dados do NANOGrav.
  Significa que esta análise não tem sensibilidade para detectá-la.
- **NÃO significa** que a HD está ausente. A HD já foi detectada
  pelo NANOGrav com metodologia adequada (optimal statistic).
  Nosso pipeline não a recupera porque não usa essa metodologia.
- **NÃO é evidência contra H17/H18.** As hipóteses do projeto
  continuam abertas. O que foi testado é o MÉTODO, não a física.

### Frase-chave (Gepeto)
> "Não devemos transformar 'não detectamos' em 'não existe'."

---

## 3. POR QUE O RESULTADO NULO ERA ESPERADO

Razões técnicas:

1. **Red noise intrínseco não modelado.** Cada pulsar tem ruído
   vermelho próprio que domina a variância em baixas frequências.
   Não modelamos isso.
2. **Sem optimal statistic.** A literatura PTA usa o optimal
   statistic (Chamberlin et al. 2015), que pondera por erros
   individuais. Não usamos isso.
3. **Sem correção de Shklovskii nem aceleração galáctica.**
4. **Reamostragem mensal** introduz correlação artificial dentro
   do mesmo bin.

A literatura de 2024-2026 (Fang et al., 2026) já reporta nulo em
teste equivalente de anisotropia correlacionada com LSS. Nosso
resultado é **consistente com a literatura**.

---

## 4. REGRA METODOLÓGICA REAFIRMADA

**Se o resultado for nulo, publicamos nulo.**
**Se for estranho, primeiro tentamos destruir o resultado antes
de tentar explicá-lo pela Grande Onda.**

---

## 5. FRAMEWORK DE TESTES (Proposta Gepeto)

Adotamos o seguinte framework de 4 camadas, para evitar falsos
positivos por deficiência do pipeline:

TESTE 1 — Pipeline + ruído
↓
não inventa sinal ✅ JÁ FEITO

TESTE 2 — Pipeline + sinal HD conhecido injetado
↓
recupera sinal conhecido ⏳ PRÓXIMO

TESTE 3 — Dados reais + modelo convencional
↓
procura resíduos/anomalias ✅ FEITO (nulo)

TESTE 4 — Hipótese Grande Onda
↓
procura assinatura específica
⏳ DEPOIS DO TESTE 2

**Regra central:** não avançar para Teste 4 sem ter passado
pelo Teste 2. Caso contrário, qualquer "anomalia" pode ser
apenas deficiência do pipeline.

---

## 6. PRÓXIMOS PASSOS

1. **`pipeline_hd.py`** — injetar HD conhecida em dados sintéticos
   com ruído realista e verificar se o pipeline a recupera.
   - Se recuperar: o pipeline funciona; sensibilidade é o gargalo.
   - Se não recuperar: o pipeline tem problema estrutural.

2. **`pipeline_optimal.py`** (fase futura) — implementar optimal
   statistic (Chamberlin et al.) e marginalização de red noise.

3. **Só então** retestar H17/H18 em dados reais.

---

## 7. OBSERVAÇÃO DA GEMINI

> "Se tivesse aparecido uma curva HD 'bonita' no gráfico sem
> esse tratamento, seria um falso positivo decorrente de
> contaminação cinemática ou bug. O pré-registro nos salvou de
> um confirmation bias!"

Isso está correto. O resultado nulo com p = 0.430 é uma
**demonstração de que o protocolo de pré-registro está
funcionando** — não uma refutação da hipótese.

---

## 8. REFERÊNCIAS

- Chamberlin, S. J., et al. (2015). "Time-domain implementation
  of the pulsar timing array optimal statistic." ApJ 810, 74.
- Fang et al. (2026). "A Template-Based Search for
  Large-Scale-Structure-Correlated Anisotropy in the Nanohertz
  Gravitational-Wave Background." arXiv.
- NANOGrav Collaboration (2023). 15yr Data Set.
- Registro de testes: `docs/registro_testes_2026-10-16.txt`.
- Pré-registro: `docs/README_preregistro.md` (commit cb4558b).

============================================================
FIM DO REGISTRO
============================================================
## 9. TESTE 2 — RECUPERAÇÃO DE HD (framework Gepeto)

### 9.1 Teste único (amplitude 5.0, sem red noise)
- r = 0.982, p = 0.000 → pipeline RECUPERA HD ✅
- Bins reproduzem a estrutura em U da HD

### 9.2 Scan sem red noise
- Limiar de detecção: SNR ≈ 1.0
- ⚠️ Anomalia: r negativo em SNR < 0.5
- Causa: seed fixa do gerador cria padrão de ruído
  idêntico entre amplitudes, produzindo falso positivo
- Lição: reforça necessidade de sky scramble em dados reais

### 9.3 Scan com red noise = 1.0
- Limiar de detecção: SNR ≈ 1.0
- Comportamento limpo: r ≈ 0 em SNR baixo, r > 0.7 em SNR ≥ 1
- Cenário realista. É o que vale para interpretar dados reais.

### 9.4 Conclusão para o resultado real
- Pipeline recupera HD em simulação quando SNR ≥ 1
- Dados reais deram r ≈ 0 → SNR efetivo < 1
- Consistente com red noise não modelado
- NÃO é evidência contra H17/H18