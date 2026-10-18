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

## HISTÓRICO

Novas atualizações devem ser adicionadas sem apagar conclusões anteriores. O Git deve preservar a evolução das ideias.
