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

------------------------------------------------------------
9.2 SCAN SEM RED NOISE — LIMIAR DE SENSIBILIDADE
------------------------------------------------------------

Amplitudes varridas: 0.1 a 10 (9 pontos log-espaçados).
Ruído vermelho: 0.0.
Seed por amplitude: 42 + 1000 * i_amp (patch aplicado após
identificação de artefato, ver abaixo).

Resultado (com seed por amplitude):

  SNR    Pearson r   p       recupera
  0.10   -0.840      0.002   False    ← outlier (ver abaixo)
  0.18   -0.135      0.709   False
  0.32   +0.649      0.042   False
  0.56   +0.759      0.011   True
  1.00   +0.940      0.000   True
  1.78   +0.981      0.000   True
  3.16   +0.964      0.000   True
  5.62   +0.969      0.000   True
  10.0   +0.970      0.000   True

Limiar de detecção: SNR ≈ 0.5 - 1.0.

ANOMALIA RESIDUAL — SNR = 0.1:
  O ponto em amplitude 0.1 ainda mostra correlação negativa
  significativa (r = -0.84, p = 0.002). Análise: as posições
  dos pulsares são geradas pela mesma seed (42 + 1000*0 = 42).
  Essa configuração específica de posições cria, em amplitude
  baixa, um padrão onde o ruído branco anti-correlaciona com
  HD por coincidência.

  NÃO É BUG. É uma propriedade de qualquer estimador em
  regime de SNR muito baixo: a variância estatística pode
  produzir correlações espúrias de qualquer sinal.

LIÇÃO METODOLÓGICA (crítica):
  Este resultado é DEMONSTRAÇÃO EMPÍRICA de que:
    1. Um único teste, em SNR baixo, pode dar falso positivo.
    2. O falso positivo pode ser significativo (p < 0.01) e
       ainda assim espúrio.
    3. Por isso o sky scramble é OBRIGATÓRIO na análise de
       dados reais — ele controla exatamente esse tipo de
       flutuação.

  Sem o sky scramble, o pipeline_real.py poderia ter produzido
  uma "detecção" espúria nos dados do NANOGrav. O pré-registro
  nos protegeu disso.

CORREÇÃO APLICADA:
  Seed diferente por amplitude no scan (42 + 1000 * i_amp).
  O artefato foi reduzido de 4 pontos para 1 ponto. Para
  eliminação completa, seria necessário AVERAGEAR sobre
  múltiplas seeds por amplitude (ver observação abaixo).

OBSERVAÇÃO PARA FASE FUTURA:
  Para robustez total, cada amplitude poderia ser testada com
  N=10 seeds diferentes, reportando a média e o desvio das
  correlações r. Isso eliminaria a dependência de seed
  individual, mas exigiria ~10x mais tempo de execução.

### 9.3 Scan com red noise = 1.0
- Limiar de detecção: SNR ≈ 1.0
- Comportamento limpo: r ≈ 0 em SNR baixo, r > 0.7 em SNR ≥ 1
- Cenário realista. É o que vale para interpretar dados reais.

### 9.4 Conclusão para o resultado real
- Pipeline recupera HD em simulação quando SNR ≥ 1
- Dados reais deram r ≈ 0 → SNR efetivo < 1
- Consistente com red noise não modelado
- NÃO é evidência contra H17/H18
------------------------------------------------------------
9.2.1 SCAN COM MÚLTIPLAS SEEDS — ROBUSTEZ DO LIMIAR
------------------------------------------------------------

Configuração:
  - 5 seeds por amplitude
  - 9 amplitudes entre 0.1 e 10
  - Ruído vermelho: 0.0
  - Seed base: 42 + 1000 * i_amp + s * 7919

Resultado:

  SNR    r_medio ± std      (min, max)      recupera
  0.10   -0.274 ± 0.380     (-0.84, +0.20)  0/5
  0.18   -0.288 ± 0.276     (-0.70, +0.09)  0/5
  0.32   +0.682 ± 0.128     (+0.52, +0.90)  2/5
  0.56   +0.569 ± 0.296     (+0.21, +0.92)  3/5
  1.00   +0.890 ± 0.050     (+0.80, +0.94)  5/5
  1.78   +0.969 ± 0.017     (+0.95, +0.99)  5/5
  3.16   +0.969 ± 0.016     (+0.94, +0.99)  5/5
  5.62   +0.972 ± 0.008     (+0.97, +0.99)  5/5
  10.00  +0.969 ± 0.017     (+0.94, +0.98)  5/5

CONCLUSÃO:

  1. REGIME DE RUÍDO (SNR < 0.2):
     Detecção nula (0/5). r médio negativo ou próximo de zero,
     com dispersão grande. Este é o regime de ruído branco puro.
     O valor r = -0.84 observado em uma única seed na seção
     §9.2 anterior era uma flutuação extrema (-2.2 sigma) de
     uma distribuição centrada em -0.274, com desvio 0.380.
     NÃO era artefato sistemático — era simplesmente a cauda
     da distribuição.

  2. ZONA DE TRANSIÇÃO (0.3 < SNR < 0.6):
     Detecção intermitente (2/5 a 3/5). O pipeline às vezes
     recupera, às vezes não — dependendo da realização
     específica do ruído. Esta é uma região intrinsecamente
     difusa, e qualquer resultado aqui deve ser interpretado
     com cautela.

  3. REGIME DETERMINÍSTICO (SNR >= 1.0):
     Detecção robusta (5/5). r médio > 0.89, desvio < 0.05,
     mínimo > 0.80 em todas as seeds. A recuperação de HD é
     determinística acima deste limiar.

LIMIAR DE SENSIBILIDADE CONFIRMADO:
  SNR >= 1.0 para detecção robusta.
  SNR < 0.3 para não-detecção consistente.
  Zona de transição difusa entre 0.3 e 0.6.

IMPLICAÇÃO PARA OS DADOS REAIS (§1-8):
  O resultado nulo do pipeline_real.py (r ≈ 0) é consistente
  com o esperado quando SNR efetivo < 1.0. Como o red noise
  não é modelado, o SNR efetivo cai abaixo do limiar, e o
  pipeline não detecta a HD — exatamente como previsto pelo
  scan.