# Gepeto — Projeto Tempo-Ondas

**Membro:** Gepeto  
**Função:** análise, crítica metodológica, organização de hipóteses e desenho de experimentos.

## Última atualização

**Data:** 2026-10-18

## Estado atual

O projeto passou por três etapas principais:

1. **Pipeline simplificado em dados reais**
   - Resultado nulo para a análise realizada.
   - Isso não foi interpretado como refutação da hipótese Tempo-Ondas.

2. **Validação com Hellings–Downs sintética**
   - O pipeline recuperou uma assinatura HD injetada.
   - O scan com 5 seeds mostrou recuperação consistente em SNR mais alto.
   - Em SNR = 1,0 houve recuperação em 5/5 seeds.
   - Em SNR baixo houve maior dispersão entre seeds.

3. **Optimal Statistic**
   - O ambiente foi migrado para WSL2 devido às limitações de memória no Windows/PINT.
   - A GTX 1050 Ti foi habilitada para os cálculos JAX.
   - Foi corrigida a leitura do modelo de ruído.
   - No teste com 5 pulsares: **SNR = +1,366** e **log10_A = -14,49**.
   - O conjunto completo de 68 pulsares está em processamento.

## FATO

- O pipeline sintético recupera HD nas condições testadas.
- A recuperação em sinal forte permaneceu consistente nas 5 seeds.
- O Optimal Statistic produziu SNR positivo no teste com 5 pulsares.
- O resultado dos 68 pulsares ainda precisa ser analisado.

## INTERPRETAÇÃO

O SNR positivo mostra que a implementação está produzindo uma estimativa positiva para o modelo utilizado no teste. Isso ainda não constitui evidência de nova física ou da hipótese Tempo-Ondas.

A diferença entre a correlação simples e o Optimal Statistic mostra a importância de uma estatística adequada aos dados de PTA.

## HIPÓTESE

Depois de reproduzir adequadamente os sinais convencionais, podemos procurar componentes residuais que não sejam explicados pelos modelos convencionais e comparar essas características com previsões específicas de H17/H18.

## ESPECULAÇÃO

A hipótese maior do projeto continua sendo a possibilidade de uma estrutura ondulatória do tempo, representada conceitualmente pela Grande Onda e por ondas menores relacionadas à estrutura temporal.

Essa ideia permanece especulativa e não deve ser confundida com os resultados atuais.

## EXPERIMENTOS / PRÓXIMOS PASSOS

1. Concluir os 68 pulsares.
2. Registrar o resultado completo e os parâmetros utilizados.
3. Comparar com a literatura.
4. Verificar a robustez da implementação do Optimal Statistic.
5. Estabelecer sensibilidade e limites superiores.
6. Somente depois testar previsões quantitativas específicas de H17/H18.

## REGRA METODOLÓGICA

> Não procurar uma confirmação da Grande Onda. Procurar primeiro descobrir se estamos errados.

Resultados inesperados devem primeiro ser testados contra bugs, ruído, seleção de dados, efeitos astrofísicos e explicações convencionais.
# Gepeto — Debate sobre o falso positivo com 20 pulsares

**Data:** 2026-10-18  
**Modo:** Debate

## Minha conclusão

Eu não escolheria A, B ou C isoladamente.

Minha preferência é **D — reduzir e validar o problema metodológico antes de executar um MCMC completo de 68 pulsares**.

O SNR = 41,31 deve ser tratado como um excelente teste de estresse do pipeline, mas **não como evidência de um sinal físico**. A própria análise do grupo identificou que o resultado é consequência do tratamento rígido dos parâmetros de ruído.

Isso é, na verdade, uma vitória metodológica: conseguimos produzir um resultado extremamente convincente e depois destruí-lo procurando uma explicação convencional.

## FATO

O pipeline oficial `discovery` foi executado com 20 pulsares e produziu:

- SNR = 41,31

A investigação posterior identificou que os parâmetros do `noisedict` estavam sendo fixados em vez de serem devidamente marginalizados através de uma cadeia estatística apropriada.

Segundo o diagnóstico atual do grupo, essa escolha tornou o modelo rígido e fez com que parte do ruído fosse interpretada como sinal.

O teste anterior com 5 pulsares havia produzido SNR ≈ 1,36 e é considerado, neste momento, um resultado metodologicamente mais confiável dentro das condições testadas.

## INTERPRETAÇÃO

O episódio mostra por que não devemos usar o valor do SNR sozinho como critério de descoberta.

Um resultado enorme pode ser matematicamente consistente com o pipeline e ainda assim ser consequência de uma especificação inadequada do modelo.

Portanto, antes de procurar qualquer assinatura relacionada à Grande Onda, precisamos garantir que o pipeline consiga distinguir:

**ruído → efeitos convencionais → sinal HD → possíveis resíduos não explicados.**

## HIPÓTESE DE TRABALHO

É possível que exista algum componente residual interessante nos dados, mas ainda não temos autorização experimental para chamá-lo de assinatura da hipótese Tempo-Ondas.

Primeiro precisamos demonstrar que o resultado permanece quando os parâmetros relevantes do modelo de ruído são tratados corretamente.

## PROPOSTA D — REDUZIR O PROBLEMA

Em vez de jogar imediatamente o MCMC completo dos 68 pulsares na máquina, proponho construir uma escada de validação:

### Etapa 1 — 5 pulsares

Reproduzir o resultado de referência com o tratamento correto dos parâmetros de ruído.

### Etapa 2 — 10 pulsares

Verificar se o comportamento permanece quando aumentamos o número de pulsares.

### Etapa 3 — 20 pulsares

Repetir o teste que produziu SNR = 41,31, mas agora com o tratamento estatístico correto.

Esse é um teste particularmente importante porque permite verificar se o falso positivo desaparece.

### Etapa 4 — 20 pulsares com diferentes seeds

Verificar a estabilidade estatística do resultado.

### Etapa 5 — 68 pulsares

Somente depois de validar as etapas anteriores tentar o dataset completo.

## SOBRE O CLOUD / COLAB

A opção C é interessante, mas eu não migraria imediatamente todo o projeto para a nuvem.

Primeiro devemos descobrir **qual é exatamente o custo computacional do MCMC correto**.

Se conseguirmos fazer uma versão reduzida funcionar em 5/10/20 pulsares, teremos uma estimativa muito melhor de quanto processamento realmente precisamos.

A partir daí podemos decidir racionalmente entre:

- processamento local durante a madrugada;
- processamento em lotes;
- Google Colab;
- outra máquina;
- ou algum serviço de computação em nuvem.

## SOBRE A OPÇÃO B

Não abandonaria a parte teórica.

Enquanto o processamento roda, podemos continuar desenvolvendo a teoria da Grande Onda, mas mantendo-a explicitamente separada dos resultados observacionais.

Isso permite que o projeto avance em duas linhas:

**Linha experimental**
→ PTA → ruído → HD → optimal statistic → resíduos → testes quantitativos.

**Linha teórica**
→ Grande Onda → ondas menores → estrutura temporal → previsões observáveis.

O momento de juntar as duas linhas será quando conseguirmos transformar uma previsão da teoria em uma estatística que possa ser procurada nos dados.

## A REGRA MAIS IMPORTANTE

> **Quanto mais extraordinário o resultado, mais maneiras precisamos encontrar de destruí-lo antes de acreditar nele.**

O SNR = 41,31 foi exatamente esse tipo de teste.

Se um resultado sobreviver a diferentes modelos de ruído, diferentes seeds, diferentes subconjuntos de pulsares e diferentes métodos estatísticos, aí sim começará a ficar interessante.

## Próximo experimento que eu escolheria

**20 pulsares + tratamento correto do ruído**, porque reproduz diretamente o caso em que apareceu o falso positivo.

Se o SNR despencar, aprendemos algo importante.

Se permanecer positivo em nível razoável, teremos um resultado muito mais interessante para investigar.

Se aumentar ou mudar de comportamento de maneira inesperada, teremos outro problema científico para atacar.

Em todos os três casos ganhamos informação.

— **Gepeto**
## HISTÓRICO# Membro: Gepeto

**Projeto:** Tempo, Ondas e Observador  
**Atualização:** 19/10/2026

---

## 1. Estado atual da investigação

O projeto continua sendo tratado como uma **investigação especulativa**, e não como uma teoria física estabelecida.

A hipótese central continua aberta:

> **O tempo poderia possuir uma estrutura ondulatória fundamental, sobre a qual fenômenos físicos e observáveis poderiam emergir como estruturas de uma ou mais ondas.**

Até o momento não existe evidência suficiente para afirmar que essa estrutura exista.

A regra principal continua sendo:

> **Quanto mais extraordinário o resultado, mais maneiras precisamos encontrar de destruí-lo antes de acreditar nele.**

---

## 2. Resultado importante do pipeline PTA

O grupo conseguiu avançar do pipeline simplificado para o `discovery`/Optimal Statistic.

### Resultado de 5 pulsares

Foi obtido:

- **SNR ≈ +1.366**
- `log10_A ≈ -14.49`

Esse resultado deve ser tratado como **validação preliminar do pipeline e do tratamento do modelo de ruído**, e não como detecção de uma nova física.

### Resultado de 20 pulsares

Foi obtido inicialmente:

- **SNR = 41.31**

O próprio grupo posteriormente conseguiu identificar uma explicação metodológica plausível para esse resultado.

Os parâmetros de ruído estavam fixados em vez de serem devidamente marginalizados/amostrados.

Portanto:

> **SNR

Novas atualizações devem ser adicionadas sem apagar conclusões anteriores. O Git deve preservar a evolução das ideias.
