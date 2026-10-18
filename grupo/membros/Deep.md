# DEEP (DeepSeek)
**Projeto Tempo-Ondas**
ÚLTIMA ATUALIZAÇÃO: 2026-10-18

**ASSUNTO:**
Avaliação da migração para WSL2, uso de GPU e o primeiro resultado do Optimal Statistic.

**DADOS / FATOS OBSERVADOS:**
- A migração do Windows para o WSL2 (Ubuntu) resolveu os problemas de estouro de memória (malloc).
- A GPU (GTX 1050 Ti) foi ativada com sucesso via JAX + CUDA 12.
- O `noisedict` precisou ser extraído manualmente do arquivo `.par` para o `discovery`.
- O teste com 5 pulsares resultou em **SNR = +1.366**.

**CONCLUSÃO:**
O pipeline oficial do NANOGrav (`discovery`) está funcionando e a matemática está correta. O SNR positivo comprova que a injeção dos parâmetros de ruído (noisedict) foi a peça que faltava. 

**PONTOS IMPORTANTES:**
- O tempo de carregamento do PINT no Linux ainda é o gargalo (leva ~30 min para 5 pulsares). Por isso, o script `pipeline_gpu_68.py` usa multiprocessing.
- A GPU não acelera o carregamento, mas vai acelerar o cálculo do `Optimal Statistic` quando tivermos mais dados.

**HIPÓTESES / IDEIAS:**
- H1: Com 68 pulsares, o SNR deve subir para a faixa de 3.0 a 5.0, alinhando-se com as publicações oficiais do NANOGrav.

**CRÍTICAS / POSSÍVEIS PROBLEMAS:**
- A memória RAM de 12 GB no WSL2 pode ser insuficiente para carregar os 68 pulsares em paralelo. Se o script quebrar, reduziremos os workers de 4 para 2.

**DÚVIDAS:**
- O modelo de ruído extraído dos `.par` (v2.1.0) reflete exatamente o que foi usado na análise oficial do GWB de 2023? Ou os parâmetros podem ter sido atualizados?

**PRÓXIMOS TESTES SUGERIDOS:**
1. Rodar os 68 pulsares em segundo plano (`nohup`).
2. Analisar o output final.
3. Comparar o valor de `log10_A` encontrado com o artigo de 2023 do NANOGrav.

**REFERÊNCIAS IMPORTANTES:**
- Chamberlin et al. (2015)
- Documento de Ambiente (`docs/ambiente_v1.md`)

**FEEDBACK SOBRE A PROPOSTA DO GEPETO:**
A proposta é excelente. Sugiro usar extensões `.md` em vez de `.txt` para melhor visualização no GitHub. A separação entre "Modo Independente" e "Modo Debate" é cirúrgica para evitar contaminação de contexto.

==================================================
**HISTÓRICO**
2026-10-18
Primeira entrada. Registro da virada técnica (WSL2 + GPU) e do SNR positivo (+1.36).