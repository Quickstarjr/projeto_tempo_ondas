# 🧪 Projeto Tempo, Ondas e Observador
## Memorando técnico — Curva de potência e calibração espectral

**Data:** 21/10/2026  
**Status:** Etapa de validação sintética concluída; auditoria estatística complementar recomendada.

### 1. Objetivo

Avaliar se o procedimento experimental detecta uma modulação espacial periódica de amplitude conhecida em catálogos sintéticos, usando a potência de Fourier no modo correspondente à injeção.

### 2. Experimento de potência

Foram executados 200 experimentos por amplitude, nas amplitudes:

`0.000, 0.005, 0.010, 0.015, 0.020, 0.030, 0.050`

Cada comparação utilizou 50 catálogos de referência sem modulação e 50 catálogos do grupo de teste. O conjunto total previsto e concluído foi de 140.000 catálogos, com sementes únicas no gerador aleatório.

Resultados de detecção:

| Amplitude | Detecções | Taxa observada |
|---:|---:|---:|
| 0,000 | 6/200 | 3,0% |
| 0,005 | 10/200 | 5,0% |
| 0,010 | 7/200 | 3,5% |
| 0,015 | 22/200 | 11,0% |
| 0,020 | 59/200 | 29,5% |
| 0,030 | 157/200 | 78,5% |
| 0,050 | 200/200 | 100,0% |

A taxa observada no controle nulo foi de 3%, compatível com o nível nominal de 5% neste conjunto de 200 comparações. A capacidade de detecção aumentou com a amplitude do sinal injetado.

### 3. Auditoria espectral

A comparação entre as potências dos modos \(+k\) e \(-k\) encontrou diferença relativa máxima de aproximadamente \(1,66\times10^{-14}\), consistente com a simetria esperada da transformada de Fourier de um campo real.

A mediana da potência no modo \(k=3\) aumentou de aproximadamente 375,9, com amplitude zero, para 19.855,8, com amplitude 0,20. Os modos vizinhos também apresentaram aumentos, embora menores em relação ao modo injetado nas amplitudes mais elevadas.

### 4. Calibração aproximada

O excesso de potência mediana no modo \(k=3\), dividido por \(A^2\), permaneceu aproximadamente entre 469.640 e 544.337 nas amplitudes examinadas.

O ajuste linear das nove médias de potência em função de \(A^2\) apresentou:

- Intercepto estimado: 637,35.
- Coeficiente de \(A^2\): 499.177,33.
- \(R^2\): 0,999610.
- RMSE das médias: 127,26 unidades de potência.

Esses resultados são compatíveis com uma resposta média aproximadamente quadrática. O \(R^2\) refere-se ao ajuste das médias por amplitude, e não representa a probabilidade de detecção nem uma medida de confirmação de uma hipótese cosmológica.

### 5. Limitações e próximos passos

1. Realizar uma auditoria adicional da incerteza do coeficiente quadrático, dos resíduos e da variância entre realizações.
2. Verificar a seletividade do modo injetado, considerando a janela de Hann, a discretização espacial e os efeitos da amostragem.
3. Reforçar os controles nulos e avaliar a calibração da taxa de falsos positivos.
4. Documentar integralmente parâmetros, sementes, versões de código e resultados.
5. Somente após os controles metodológicos, definir um protocolo independente para testar previsões previamente especificadas em dados astronômicos reais.

### 6. Conclusão

Os testes demonstram recuperação de uma modulação espacial artificial em catálogos sintéticos e uma resposta espectral que cresce aproximadamente com o quadrado da amplitude injetada.

**O resultado valida parcialmente o procedimento de detecção sintética. Não demonstra a existência de ondas temporais cosmológicas nem constitui, por si só, evidência observacional de uma nova física.**

A recomendação é preservar os resultados atuais como marco reproduzível do projeto e avançar para uma auditoria estatística complementar, sem modificar retroativamente o experimento já concluído.