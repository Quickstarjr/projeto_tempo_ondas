# Experimento: estrela_KIC757450

![curva_luz.png](https://raw.githubusercontent.com/Quickstarjr/projeto_tempo_ondas/main/outputs/reports/estrela_KIC757450/curva_luz.png)

![periodograma_ls.png](https://raw.githubusercontent.com/Quickstarjr/projeto_tempo_ondas/main/outputs/reports/estrela_KIC757450/periodograma_ls.png)

![periodograma_bls.png](https://raw.githubusercontent.com/Quickstarjr/projeto_tempo_ondas/main/outputs/reports/estrela_KIC757450/periodograma_bls.png)


## Análise Preliminar
Este experimento processou os dados brutos da estrela KIC 757450.
O método BLS encontrou um possível trânsito com período de **18.80 dias**.

### Próximos passos
Aguardando análise quantitativa do CSV e LOG pelos membros do grupo (Grokinha e Gemini).
## Análise Quantitativa (Leitura da Grokinha)

### Dados Analisados
- **Alvo:** KIC 757450
- **Missão:** Kepler
- **Pontos utilizados:** 1624 (após remoção de outliers)
- **Cobertura temporal:** BKJD 131.5 a 165 (~33.5 dias)
- **Período BLS detectado:** 18.80 dias
- **Potência BLS:** ~1.37 × 10⁴

### Interpretação Cautelosa
O método BLS encontrou um candidato com período de 18.80 dias. No entanto, a cobertura temporal é de apenas ~33.5 dias, o que representa **menos de 2 ciclos completos** do período detectado. 

Nesta situação, o sinal pode ser resultado de:
1. Rotação estelar (manchas solares).
2. Um harmônico da frequência de rotação.
3. Um artefato da janela de observação (curto período de dados).

### Próximos Testes Recomendados
1. Baixar todos os quarters disponíveis de KIC 757450 e repetir o BLS.
2. Comparar o período BLS com o período de rotação obtido pelo Lomb-Scargle.
3. Plotar a curva de luz "dobrada" (phase-folded) em 18.8 dias para ver a forma do dip.

### Conclusão Preliminar
Há um sinal interessante em 18.80 dias, mas ainda é cedo para afirmar se é trânsito planetário. A análise expandida com todos os quarters é necessária.

## Teste Avançado: Phase Folding (Curva Completa)
**Data:** 2026-10-20

Após a suspeita levantada pela Grokinha sobre a curta janela de observação, baixamos todos os quarters disponíveis do Kepler para a KIC 757450 (cobrindo ~1500 dias) e realizamos o *Phase Folding* no período de 18.80 dias.

### Resultado Visual
- A curva dobrada não apresentou nenhuma estrutura coerente (nem "V" nem "U").
- Os dados se apresentaram como uma nuvem dispersa de ruído.

### Conclusão Científica
O período de 18.80 dias detectado pelo BLS inicial era um **falso positivo** (provavelmente um artefato da janela curta de observação ou um harmônico da rotação estelar). **Não há evidência de trânsito planetário** neste sinal. 

Esta é a prova de que a abordagem do "Kit Quíntuplo" e o ceticismo do grupo (Grokinha e Gepeto) são essenciais. A "descoberta" foi destruída por testes adicionais antes de ser anunciada.