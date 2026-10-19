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

## Histórico

**2026-10-18**  
Primeira entrada. Posição sobre SNR 41.31 como falso positivo e recomendação híbrida (documentar 5 pulsares + explorar nuvem).

**2026-10-19**  
Atualização. Inclusão da contribuição sobre Dusty Plasmas para a Gaveta de Física. Confirmação de que a fase pesada de MCMC fica em pausa.
