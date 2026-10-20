# GROKINHA

**Projeto Tempo-Ondas**  
**Última Atualização:** 2026-10-19  
**Versão do Projeto:** V5.2 + Gaveta de Física

---

## Assunto
1. Posição sobre o falso positivo do SNR 41.31 e limitações de hardware.  
2. Contribuição para a Gaveta de Física: Dusty Plasmas.  
3. Estado atual da colaboração.

---

## 1. Dados / Fatos Observados (Pipeline PTA)

- Pipeline `discovery` rodou com 20 pulsares e produziu SNR = 41.31.
- Esse valor é inconsistente com a literatura do NANOGrav 15yr (SNR típico ~3–5 com ~68 pulsares).
- Causa identificada: parâmetros de ruído (`noisedict`) fixos, sem marginalização MCMC.
- Resultado anterior com 5 pulsares: SNR ≈ +1.366 (único resultado minimamente confiável até o momento).
- Hardware local (i7-2600, HDD, 16 GB RAM) e Colab free não suportam MCMC completo dos 68 pulsares.

---

## 2. Conclusão (Pipeline PTA)

O SNR 41.31 é um **falso positivo**.  
O resultado sólido a ser documentado e congelado é o dos **5 pulsares (SNR ≈ +1.366)**.  
A fase pesada de Optimal Statistic com marginalização fica em pausa até haver hardware adequado ou estratégia mais leve.

---

## 3. Contribuição — Gaveta de Física: Dusty Plasmas

### O que são
Plasmas de baixa temperatura (RF ou DC) contendo partículas sólidas de tamanho micrômetro. As partículas se carregam e interagem via potencial de Yukawa, formando cristais, líquidos complexos, filamentos e voids.

### Fenômenos relevantes
- **Voids**: regiões estáveis sem poeira, com bordas nítidas, geradas pelo balanço entre força eletrostática e ion drag.
- **Cristais de plasma e filamentos**: ordenação espacial espontânea; em microgravidade (ISS – PK-3 Plus / PK-4) formam estruturas 3D e fases tipo cristal líquido.
- **Dust Acoustic Waves**: ondas de densidade que podem induzir aglomeração de partículas.
- **Auto-organização**: padrões de alta/baixa densidade, grades alinhadas a malhas, estruturas convectivas.

### Relevância para o projeto
Sistema laboratorial controlável de partículas carregadas em meio ondulatório/ionizado. Produz voids, filamentos e nós de densidade de forma espontânea — analogia qualitativa útil para a distribuição de matéria na cosmic web e para dinâmicas do universo primordial.

### Limitações
Analogia qualitativa, não quantitativa. Escalas, energias e composição são completamente diferentes das cosmológicas.

### Referências-chave
- Experimentos PK-3 Plus e PK-4 (ISS)
- Literatura de voids (Morfill, Goree, Tsytovich et al.)
- Revisões de complex plasmas em microgravidade

---

## 4. Pontos Importantes

- A regra “primeiro tente destruir o resultado” funcionou corretamente com o SNR 41.31.
- A nova Gaveta de Física (experimentos reais) é o lugar correto para catalogar Dusty Plasmas, Chladni e outros sistemas terrestres.
- Meu papel atual: revisão independente + busca de contradições na literatura + contribuições para a Gaveta de Física.

---

## 5. Próximos Passos Sugeridos

1. Documentar formalmente o resultado dos 5 pulsares como linha de base.
2. Manter a frente teórica e a Gaveta de Física ativas enquanto o hardware limita a parte empírica pesada.
3. Reavaliar Colab ou outras nuvens apenas com estratégias de redução de memória (subconjuntos menores, menos amostras MCMC).

---
# GROKINHA

**Projeto Tempo-Ondas**  
**Última Atualização:** 2026-10-20  
**Versão do Projeto:** V5.2 + Gaveta de Física + Pivot de Baixo Custo

---

## Assunto
1. Posição sobre o falso positivo do SNR 41.31 e limitações de hardware.  
2. Contribuição para a Gaveta de Física: Dusty Plasmas.  
3. Pivot para análises leves (ciclos estelares).  
4. Falso positivo estelar (KIC 757450) destruído por phase folding.

---

## 1. Dados / Fatos Observados (Pipeline PTA)

- Pipeline `discovery` rodou com 20 pulsares e produziu SNR = 41.31.
- Esse valor é inconsistente com a literatura do NANOGrav 15yr (SNR típico ~3–5 com ~68 pulsares).
- Causa identificada: parâmetros de ruído (`noisedict`) fixos, sem marginalização MCMC.
- Resultado anterior com 5 pulsares: SNR ≈ +1.366 (único resultado minimamente confiável até o momento).
- Hardware local (i7-2600, HDD, 16 GB RAM) e Colab free não suportam MCMC completo dos 68 pulsares.
- Tentativa de MCMC local com 2 pulsares: taxa de aceitação 0%.

---

## 2. Conclusão (Pipeline PTA)

O SNR 41.31 é um **falso positivo**.  
O resultado sólido a ser documentado e congelado é o dos **5 pulsares (SNR ≈ +1.366)**.  
A fase pesada de Optimal Statistic com marginalização fica **congelada** por limitação de hardware.  
O projeto redirecionou o foco para análises de baixo custo computacional.

---

## 3. Contribuição — Gaveta de Física: Dusty Plasmas

### O que são
Plasmas de baixa temperatura (RF ou DC) contendo partículas sólidas de tamanho micrômetro. As partículas se carregam e interagem via potencial de Yukawa, formando cristais, líquidos complexos, filamentos e voids.

### Fenômenos relevantes
- **Voids**: regiões estáveis sem poeira, com bordas nítidas, geradas pelo balanço entre força eletrostática e ion drag.
- **Cristais de plasma e filamentos**: ordenação espacial espontânea; em microgravidade (ISS – PK-3 Plus / PK-4) formam estruturas 3D e fases tipo cristal líquido.
- **Dust Acoustic Waves**: ondas de densidade que podem induzir aglomeração de partículas.
- **Auto-organização**: padrões de alta/baixa densidade, grades alinhadas a malhas, estruturas convectivas.

### Relevância para o projeto
Sistema laboratorial controlável de partículas carregadas em meio ondulatório/ionizado. Produz voids, filamentos e nós de densidade de forma espontânea — analogia qualitativa útil para a distribuição de matéria na cosmic web e para dinâmicas do universo primordial.

### Limitações
Analogia qualitativa, não quantitativa. Escalas, energias e composição são completamente diferentes das cosmológicas.

---

## 4. Pivot para Análises Leves + Kit Quíntuplo

O grupo adotou a estrutura padronizada de experimentos (Kit Quíntuplo):
- `dados.csv`
- `resultado.json`
- `execucao.log`
- gráficos `.png` (com links Raw)
- `interpretacao.md`

Primeiro experimento da nova linha: **KIC 757450** (estrela tipo-Sol, Kepler).

---

## 5. Falso Positivo Estelar (KIC 757450) — 2026-10-20

### Fatos
- BLS em trecho curto (~33 dias, 1624 pontos) detectou candidato em **18,80 dias** (potência ~1,37×10⁴).
- Cobertura temporal insuficiente (< 2 ciclos).
- Phase folding com a curva completa (~1500 dias) **não mostrou estrutura coerente** de trânsito (nuvem de ruído).

### Conclusão
O período de 18,80 dias era um **falso positivo** (artefato da janela curta ou harmônico de rotação).  
Não há evidência de trânsito planetário neste sinal.

### Lição metodológica
O mesmo filtro que destruiu o SNR 41.31 funcionou de novo:
1. Detecção inicial interessante  
2. Análise cautelosa (cobertura insuficiente)  
3. Teste de estresse (phase folding completo)  
4. Sinal destruído e registrado com honestidade  

A regra “primeiro tente destruir o resultado” continua válida e operacional.

---

## 6. Pontos Importantes

- A regra “primeiro tente destruir o resultado” funcionou corretamente no PTA (SNR 41.31) e no experimento estelar (18,80 dias).
- A nova Gaveta de Física e o Kit Quíntuplo são as ferramentas corretas para a fase de baixo custo.
- Meu papel atual: revisão independente + busca de contradições + contribuições para a Gaveta de Física + leitura quantitativa de experimentos leves.

---

## 7. Próximos Passos Sugeridos

1. Manter o pipeline PTA pesado congelado.
2. Expandir a linha de ciclos/rotação estelar com mais estrelas e cobertura temporal completa.
3. Continuar alimentando a Gaveta de Física e a Gaveta Filosófica.
4. Documentar cada experimento com o Kit Quíntuplo completo.

---

## Histórico

**2026-10-18**  
Primeira entrada. Posição sobre SNR 41.31 como falso positivo e recomendação híbrida (documentar 5 pulsares + explorar nuvem).

**2026-10-19**  
Atualização. Inclusão da contribuição sobre Dusty Plasmas para a Gaveta de Física. Confirmação de que a fase pesada de MCMC fica em pausa.

**2026-10-20**  
Atualização. Registro do pivot para análises leves. Documentação do falso positivo estelar em KIC 757450 (18,80 dias) destruído por phase folding com curva completa. Reforço da regra metodológica de destruição de candidatos antes de celebrá-los.

## Histórico

**2026-10-18**  
Primeira entrada. Posição sobre SNR 41.31 como falso positivo e recomendação híbrida (documentar 5 pulsares + explorar nuvem).

**2026-10-19**  
Atualização. Inclusão da contribuição sobre Dusty Plasmas para a Gaveta de Física. Confirmação de que a fase pesada de MCMC fica em pausa.
