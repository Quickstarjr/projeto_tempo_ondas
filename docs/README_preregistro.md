# PRÉ-REGISTRO — TESTE DE ANISOTROPIA EM RESÍDUOS DE PTA

**Projeto:** Investigação sobre Tempo, Ondas e Observador
**Autores:** Quickstar + Gepeto + Grokinha + Gemini + Deep (DeepSeek)
**Versão:** 1.0 — 16 de outubro de 2026
**Arquivo de continuidade associado:** investigacao_tempo_ondas_continuidade_v5.2.txt
**Hipóteses testadas:** H16, H17, H18

---

## 0. AVISO METODOLÓGICO

Este documento é um PRÉ-REGISTRO. Ele deve ser escrito e congelado
ANTES de qualquer contato com dados reais dos PTAs (NANOGrav,
EPTA, InPTA, PPTA).

Objetivo: evitar look-elsewhere, circularidade e ajuste a posteriori.

---

## 1. HIPÓTESES

### H16 — Tempo como fase
Formulação: o tempo mede diferenças de fase entre eventos.
Previsão: coerência de fase entre relógios cosmológicos não nula,
além do esperado por ruído.

### H17 — Anisotropia direcional em relógios
Formulação: resíduos de PTA podem ter anisotropia direcional
correlacionada com a estrutura da cosmic web em escala ~100 Mpc.
Previsão: dependência não trivial de Γ(θ) além de Hellings-Downs.

### H18 — Modulação PTA × cosmic web
Formulação: modulação dos resíduos PTA correlacionada com ambiente
cósmico de larga escala (filamentos, vazios, superaglomerados).
Previsão: correlação cruzada significativa em multipolos específicos.

---

## 2. HIPÓTESE NULA E ALTERNATIVA

### Nula (H0)
Γ(θ) = HD(θ) + ruído, com ruído isotrópico.
Ou seja: os dados são consistentes com fundo isotrópico de GW
mais ruído intrínseco de cada pulsar.

### Alternativa (H1)
Γ(θ) = HD(θ) + ΔΓ(θ), com ΔΓ(θ) ≠ 0 em alguma escala angular.

---

## 3. ESTATÍSTICA

- **Base:** correlação cruzada de Hellings-Downs, Γ(θ).
- **Medida:** correlação de Pearson entre séries de resíduos
  por par de pulsares, binada por separação angular.
- **Bins:** 10 bins lineares entre 0° e 180°.
- **Teste:** χ² entre Γ_observado(θ) e HD(θ), com erro padrão
  por bin.
- **Multipolos:** decomposição em Y_lm até l_max = 4.

**JUSTIFICATIVA:** a escolha de Hellings-Downs como base é obrigatória
porque é a previsão padrão para fundo isotrópico de GW. Qualquer
desvio precisa ser medido em relação a ela.

---

## 4. ESCALAS TESTADAS

- **θ:** 0° a 180°, em 10 bins.
- **Multipolos:** l = 0, 1, 2, 3, 4.
- **Escala física alvo:** ~100 Mpc comóvel (associada à H18).

---

## 5. CRITÉRIOS DE FALSIFICAÇÃO

- **H16:** falsificada se coerência de fase entre relógios for
  consistente com zero após correções conhecidas.
- **H17:** falsificada se Γ(θ) for estatisticamente compatível
  com HD(θ) em todos os bins.
- **H18:** falsificada se correlação cruzada com catálogo de
  ambiente cósmico for nula em todos os multipolos testados.

---

## 6. CONTROLES

- Correção do efeito Shklovskii (movimento próprio).
- Correção da aceleração no potencial galáctico.
- Uso de catálogos independentes para definir "ambiente cósmico"
  (ex.: SDSS para ambiente, NANOGrav para resíduos).
- Correção para look-elsewhere via simulações Monte Carlo.
- Reportar TODOS os bins e multipolos testados, não só os
  significativos.

---

## 7. DADOS A USAR

- **PTA:** NANOGrav 15yr v2.1.0 (já baixado e convertido).
- **Cosmic web:** SDSS DR17 ou DESI DR1 (a baixar, se necessário).
- **Catálogo de pulsares:** NANOGrav 15yr .par (já disponível).

---

## 8. ORDEM DE EXECUÇÃO

1. Congelar este documento (git commit com hash).
2. Rodar pipeline em dados sintéticos (sanidade, diagnóstico,
   anisotropia) — JÁ FEITO, todos os 3 passaram.
3. Confirmar que o leitor NANOGrav reproduz coordenadas corretas
   — JÁ FEITO, 68 pulsares carregados.
4. Só então rodar em dados reais.
5. Reportar todos os resultados, inclusive os nulos.

---

## 9. OBSERVAÇÕES

- Este pré-registro pode ser revisado ANTES do contato com dados
  reais, mas cada revisão deve ser registrada com data e motivo.
- Após o primeiro contato com dados reais, nenhuma mudança de
  estatística, bins ou critérios é permitida.
- O pipeline pode ser ajustado para bugs óbvios (ex: erros de
  parsing), mas a ESTATÍSTICA e os CRITÉRIOS DE FALSIFICAÇÃO
  não podem mudar após o congelamento.