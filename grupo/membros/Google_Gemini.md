# Membro: Google Gemini

**Modelo registrado:** Google Gemini 1.5 Pro / Flash (Google DeepMind)
**Projeto:** Tempo-Ondas
**Última atualização deste registro:** 2026-10-22

---

## 1. Papel e escopo das contribuições

Este documento consolida as contribuições registradas do Google Gemini para o projeto Tempo-Ondas.

Os temas abordados incluem:

- análise exploratória de catálogos astronômicos do SDSS;
- investigação de possíveis diferenças espaciais associadas à classificação de galáxias;
- análise de vizinhos próximos, densidade espacial e segregação;
- métodos de KDE, wavelets e análise topológica de dados (TDA);
- testes sintéticos, calibração estatística e controle de falsos positivos;
- análise espectral tridimensional e espectro de potência;
- auditoria metodológica e planejamento de análises confirmatórias.

**Regra de leitura:** os registros históricos documentam propostas, interpretações e resultados relatados durante o desenvolvimento. A inclusão neste arquivo não significa, por si só, que cada resultado tenha sido reproduzido independentemente ou validado por todos os membros do grupo.

---

## 2. Resumo do estado metodológico

O projeto percorreu uma fase exploratória, desenvolveu instrumentos de análise sintética e passou a investigar a robustez estatística dos resultados obtidos em dados astronômicos.

A prioridade atual é distinguir três categorias:

1. **Resultado reproduzido:** existe script, configuração, dados identificados e saída verificável.
2. **Resultado reportado, ainda sujeito a auditoria:** existe um registro de resultado, mas a reprodução independente ou a verificação integral dos dados ainda precisa ser concluída.
3. **Hipótese ou proposta:** método ou interpretação a ser investigado, sem confirmação empírica estabelecida.

Essa distinção deve ser mantida em todos os relatórios, memorandos e mensagens do grupo.

---

## 3. Histórico das contribuições

### 3.1. 2026-10-20 — Exploração de segregação espacial e massa

As primeiras interpretações registradas discutiram visualizações bidimensionais e tridimensionais de galáxias do SDSS.

Foi levantada a hipótese de que galáxias classificadas como mais massivas e galáxias menores poderiam apresentar distribuições espaciais diferentes, eventualmente relacionadas a padrões de densidade, filamentos e regiões de menor densidade.

O registro inicial interpretou algumas visualizações como possíveis padrões semelhantes aos observados em experimentos de Chladni.

Também foi proposta a investigação de ferramentas de análise topológica, incluindo curvas de Betti e persistência, para estudar estruturas espaciais em diferentes escalas.

**Limites:** uma semelhança visual com padrões de Chladni não demonstra que o mesmo mecanismo físico esteja operando no universo. A classificação de galáxias, a qualidade do catálogo, os efeitos de seleção e a significância estatística precisam ser estabelecidos separadamente.

**Referências registradas:**
- `outputs/reports/galaxias_tamanho/`
- `outputs/reports/galaxias_espectro_potencia/`
- `grupo/interacao/2026-10-21_validacao_chladni.md`

### 3.2. 2026-10-20 — TDA, KDE e limitações de amostragem

Foi registrada uma tentativa de identificar anéis, vazios e outras estruturas por meio de análise topológica.

O resultado exploratório foi considerado limitado pela esparsidade dos dados disponíveis. O registro menciona um conjunto de aproximadamente 8 mil galáxias em um volume de referência de 300 Mpc por lado.

Como alternativa, foram propostas:

- estimativa de densidade por *Kernel Density Estimation* (KDE) em três dimensões;
- análise de persistência topológica, incluindo componentes e cavidades;
- uso de wavelets para procurar estruturas em diferentes escalas;
- investigação de escalas da ordem de 100–150 Mpc.

Essas escalas foram propostas para investigação, não estabelecidas como detecções confirmadas.

**Próximo passo metodológico:** avaliar se as estruturas recuperadas permanecem estáveis diante de alterações justificadas nos parâmetros, nos dados e nos controles nulos.

### 3.3. 2026-10-21 — Organização do projeto e arquitetura de ferramentas

Foi discutida a organização da documentação, da biblioteca do projeto e dos mecanismos locais de encaminhamento de tarefas para os diferentes modelos.

Entre as propostas registradas estavam:

- organização da documentação em `biblioteca/`;
- registro das responsabilidades e contribuições dos membros;
- roteamento local de prompts e tarefas;
- separação entre ferramentas de análise, documentação e execução experimental.

Essas propostas são de arquitetura e organização do projeto. Sua implementação deve ser verificada diretamente no repositório antes de serem descritas como funcionalidades concluídas.

### 3.4. 2026-10-21 — Análise de vizinhos próximos

Foi registrada uma comparação entre distâncias médias de vizinhos próximos para duas categorias de galáxias.

Os valores reportados foram:

- galáxias classificadas como mais massivas: aproximadamente 2,31 Mpc;
- galáxias classificadas como anãs: aproximadamente 2,66 Mpc.

A diferença reportada motivou uma investigação estatística de possível segregação espacial.

Em registros posteriores, foi mencionada uma diferença de aproximadamente 0,3559 Mpc e um valor-p inferior a 0,0001 em um teste de permutação.

**Estado:** esses números devem ser tratados como resultados reportados até que o script, a definição das amostras, a estatística utilizada e a distribuição nula sejam conferidos e reproduzidos.

A diferença entre médias não demonstra, isoladamente, uma causa física ou uma relação com a hipótese Tempo-Ondas.

**Referências registradas:**
- `src/galaxias_estatistica_massa.py`
- `outputs/reports/galaxias_estatistica_massa/`
- `grupo/interacao/2026-10-21_validacao_chladni.md`

### 3.5. 2026-10-21 — Wavelets e teste sintético v2

Foi proposta uma mudança na análise de padrões sintéticos: substituir a abordagem baseada em Haar (`db1`) por um kernel Mexican Hat, também conhecido como função Ricker, para investigar padrões mais suaves e aproximadamente isotrópicos.

O objetivo era comparar a resposta do método em:

- padrões sintéticos do tipo Chladni com ruído;
- manchas aleatórias sem a estrutura pretendida;
- configurações de sinal e fundo com diferentes amplitudes.

A motivação era investigar a sensibilidade do instrumento e sua capacidade de produzir falsos positivos quando aplicado a dados sem o padrão-alvo.

A escolha do kernel, por si só, não valida o método. A avaliação depende dos resultados dos controles, da definição prévia da métrica e da estabilidade diante de diferentes realizações.

**Referências registradas:**
- `src/teste_wavelet_sintetico_v2.py`
- `src/teste_wavelet_metricas.py`
- `src/galaxias_kde_wavelet.py`
- `outputs/reports/teste_wavelet_sintetico_v2/`
- `outputs/auditoria/`

### 3.6. 2026-10-21 — Métricas, SNR e comparação entre dados reais e nulos

Foi proposta uma comparação sistemática entre o comportamento do pipeline em dados reais e em conjuntos de controle.

Os objetivos registrados incluíam:

- calcular métricas quantitativas de detecção e relação sinal-ruído (SNR);
- auditar os mapas produzidos;
- comparar os resultados com distribuições nulas;
- verificar se estruturas em escalas maiores persistem nos dados reais;
- evitar interpretar uma visualização isolada como evidência estatística.

A análise deve informar a métrica principal, a escala pesquisada, a definição do controle nulo, o número de realizações e a correção aplicada quando várias escalas ou configurações são examinadas.

**Referência registrada:** `src/teste_wavelet_metricas.py`.

### 3.7. 2026-10-21 — Pipeline tridimensional e espectro de potência

Um registro do Gemini relatou uma análise tridimensional envolvendo aproximadamente 35.183 galáxias do SDSS, com uso de FFT e estimativa de espectro de potência \(P(k)\).

O mesmo registro mencionou possíveis excessos de potência em relação aos controles e discutiu a escala característica das oscilações acústicas de bárions (BAO), em torno de 150 Mpc.

Esses pontos constituem um histórico de resultados relatados e interpretações exploratórias. Não devem ser apresentados como confirmação de uma nova estrutura cosmológica sem auditoria dos dados, das unidades, da seleção observacional, dos controles e da incerteza estatística.

Em particular:

- o número de objetos deve ser conferido no catálogo efetivamente utilizado;
- a geometria e a máscara observacional devem ser consideradas;
- o espectro deve ser comparado com controles apropriados;
- a interpretação da BAO deve ser compatível com a definição das coordenadas e do espectro;
- qualquer excesso precisa ser avaliado em relação às escolhas de análise e às múltiplas comparações realizadas.

**Referências registradas:**
- `outputs/reports/galaxias_espectro_potencia/`
- `src/galaxias_kde_wavelet.py`
- `src/teste_wavelet_metricas.py`

### 3.8. 2026-10-21 — Calibração sintética de falsos positivos

Foi registrado um experimento de calibração que variou a amplitude do sinal sintético, incluindo a condição de amplitude zero.

Uma atualização mencionou sete amplitudes, 200 comparações por amplitude e uma taxa de falsos positivos de 9 em 200 na condição nula, equivalente a 4,5%.

O registro também mencionou uma correção de colisão de sementes aleatórias.

A interpretação correta é que a taxa observada de 4,5% é compatível com uma taxa nominal de 5% naquele experimento. Esse resultado isolado não garante que o método esteja calibrado em todas as escalas, orientações, condições de ruído ou configurações analíticas.

**Referências registradas:**
- `src/teste_wavelet_metricas.py`
- relatórios de auditoria sob `outputs/reports/`

### 3.9. 2026-10-22 — Auditoria com 1.000 realizações

Uma atualização posterior relatou testes de controle nulo com 1.000 realizações para duas configurações identificadas como \(k=3\) e \(k=6\).

Resultados registrados:

- \(k=3\): 48 falsos positivos em 1.000 realizações, ou 4,8%; intervalo de confiança de Wilson informado: 3,6%–6,3%.
- \(k=6\): 49 falsos positivos em 1.000 realizações, ou 4,9%; intervalo de confiança de Wilson informado: 3,7%–6,4%.

Os valores relatados são compatíveis com uma taxa nominal de falsos positivos de 5%, dentro da incerteza amostral apresentada.

Essa calibração se aplica às condições específicas dos experimentos executados. Não demonstra imunidade geral a falsos positivos nem resolve automaticamente os efeitos de múltiplas escalas, orientações ou escolhas de análise.

Foram propostas verificações adicionais:

- isotropia entre os eixos X, Y e Z;
- testes com rotações diagonais;
- resposta em frequência;
- controles por embaralhamento espacial ou de fase;
- protocolo confirmatório com escolhas analíticas predefinidas.

**Referências registradas:**
- `src/teste_taxa_falsos_positivos_1000.py`
- `outputs/reports/taxa_falsos_positivos_1000/`

### 3.10. 2026-10-22 — Revisão confirmatória e qualidade do catálogo

A revisão metodológica mais recente propôs uma transição gradual da exploração para testes confirmatórios.

As recomendações registradas foram:

1. Investigar uma amostra de volume limitado com critérios de seleção bem documentados.
2. Evitar tratar magnitude aparente como substituto direto de massa estelar.
3. Investigar catálogos com estimativas de massa estelar, incluindo a possibilidade de utilizar dados MPA-JHU, verificando identificadores, unidades, cobertura e qualidade.
4. Quantificar correspondências, objetos ausentes, duplicatas e cobertura após cruzar catálogos.
5. Considerar a função de correlação de dois pontos de Landy–Szalay com catálogos aleatórios que representem a máscara angular e a seleção radial.
6. Definir previamente a estatística principal, a hipótese nula, a direção do teste e o tratamento de comparações múltiplas.
7. Formular uma previsão quantitativa da hipótese Tempo-Ondas que possa ser distinguida das explicações convencionais e dos efeitos de seleção.
8. Definir resultados que enfraqueceriam ou falsificariam a hipótese investigada.

A função de correlação de Landy–Szalay não corrige automaticamente uma máscara inadequada: o catálogo aleatório precisa representar de maneira apropriada a geometria e a seleção do levantamento.

Da mesma forma, um resultado nulo em uma análise específica não falsifica automaticamente qualquer modelo de ondas. A previsão a testar precisa estar definida com precisão.

**Estado:** protocolo proposto; execução e validação de cada etapa precisam ser documentadas.

---

## 4. Auditoria de efeitos de borda — 2026-10-22

### 4.1. Resultados reportados

A auditoria de grid regular comparou o resultado obtido com todas as células elegíveis com o resultado após a exclusão das células periféricas.

**Grid completo:**
- amplitude máxima observada: 13,6646 pontos percentuais;
- valor-p empírico reportado: 0,000200.

**Somente células interiores:**
- amplitude máxima observada: 2,4948 pontos percentuais;
- valor-p empírico reportado: 0,421316;
- mediana da distribuição nula: 2,4095 pontos percentuais;
- percentil 95 da distribuição nula: 3,3216 pontos percentuais;
- percentil 99 da distribuição nula: 3,7787 pontos percentuais.

O registro informa 5.000 permutações por análise.

### 4.2. Interpretação

A diferença encontrada no grid completo não se mantém após a exclusão das células periféricas. No teste interior, o contraste observado não é estatisticamente significativo em relação à distribuição nula utilizada.

Isso indica que o resultado original depende fortemente das regiões periféricas do grid e não deve ser tratado, isoladamente, como evidência robusta de segregação espacial associada à hipótese Tempo-Ondas.

A auditoria não prova que toda a diferença original seja causada exclusivamente por artefatos. Excluir as bordas é um diagnóstico de robustez, não uma correção completa da máscara observacional, da geometria ou dos efeitos de seleção do levantamento.

Também permanecem relevantes as limitações do catálogo, os critérios usados para classificar os objetos e as escolhas exploratórias realizadas durante a análise.

### 4.3. Próximas ações

- Versionar os scripts e relatórios pertinentes no Git após revisar os arquivos que serão incluídos.
- Verificar a procedência, a cobertura e a qualidade do catálogo de massa estelar.
- Examinar os critérios de seleção e os efeitos da máscara observacional.
- Definir previamente as estatísticas principais e os controles para as próximas análises.
- Manter os resultados exploratórios separados dos resultados confirmatórios.

**Referências:**
- `src/auditoria_grade_sem_bordas.py`
- `outputs/reports/galaxias_tamanho/auditoria_grade_sem_bordas/`
- `outputs/reports/galaxias_tamanho/auditoria_permutacao_global_grade_regular/`
- Memorando Gepeto — *O teste de robustez mudou nossa interpretação* (22/10/2026).

---

## 5. Plano de trabalho consolidado

### Prioridade A — Reprodutibilidade

- Conferir os scripts e os relatórios correspondentes a cada resultado citado.
- Registrar parâmetros, sementes aleatórias, versões de dados e número de realizações.
- Garantir que os valores dos documentos correspondam às saídas efetivas dos scripts.
- Documentar divergências ou resultados que não possam ser reproduzidos.

### Prioridade B — Qualidade e seleção dos dados

- Verificar a origem e a cobertura dos catálogos utilizados.
- Separar magnitude aparente, magnitude absoluta e estimativas de massa estelar.
- Quantificar perdas e duplicatas no cruzamento entre catálogos.
- Investigar a máscara observacional e a seleção radial.
- Evitar conclusões físicas baseadas somente em mapas visuais.

### Prioridade C — Validação estatística

- Fixar a estatística principal antes do teste confirmatório.
- Definir controles nulos que preservem as propriedades relevantes dos dados.
- Registrar a incerteza Monte Carlo dos valores-p.
- Corrigir adequadamente as comparações múltiplas quando aplicável.
- Testar robustez a bordas, orientações, escalas e parâmetros.
- Documentar resultados negativos com o mesmo cuidado dedicado aos resultados positivos.

### Prioridade D — Hipótese Tempo-Ondas

- Formular previsões quantitativas específicas.
- Comparar as previsões com explicações convencionais e efeitos de seleção.
- Estabelecer antecipadamente quais resultados favoreceriam, enfraqueceriam ou falsificariam cada previsão.
- Não tratar semelhanças visuais, resultados sintéticos ou diferenças estatísticas isoladas como comprovação da hipótese cosmológica.

---

## 6. Índice consolidado de referências

Os caminhos abaixo foram mencionados nas atualizações históricas. Sua existência, conteúdo e correspondência com os resultados devem ser conferidos no repositório.

### Scripts de análise e calibração

- `src/galaxias_estatistica_massa.py`
- `src/galaxias_kde_wavelet.py`
- `src/teste_wavelet_metricas.py`
- `src/teste_wavelet_sintetico_v2.py`
- `src/teste_taxa_falsos_positivos_1000.py`
- `src/auditoria_grade_sem_bordas.py`

### Relatórios

- `outputs/reports/galaxias_tamanho/`
- `outputs/reports/galaxias_espectro_potencia/`
- `outputs/reports/galaxias_estatistica_massa/`
- `outputs/reports/teste_wavelet_sintetico_v2/`
- `outputs/reports/taxa_falsos_positivos_1000/`
- `outputs/reports/galaxias_tamanho/auditoria_grade_sem_bordas/`
- `outputs/reports/galaxias_tamanho/auditoria_permutacao_global_grade_regular/`
- `outputs/auditoria/`

### Documentação do projeto

- `grupo/interacao/2026-10-21_validacao_chladni.md`
- Memorando Gepeto — *O teste de robustez mudou nossa interpretação* (22/10/2026)
- Repositório: `Quickstarjr/projeto_tempo_ondas`

---

## 7. Critério de atualização deste documento

Este arquivo é o registro consolidado das contribuições atribuídas ao Google Gemini, não um relatório de validação automática do projeto.

Nas próximas atualizações:

- acrescentar somente contribuições novas ou correções relevantes;
- atualizar a seção correspondente em vez de repetir o documento inteiro;
- incluir caminhos concretos de scripts e relatórios;
- identificar explicitamente resultados reproduzidos, resultados pendentes e hipóteses;
- registrar mudanças de interpretação quando uma auditoria alterar a conclusão anterior;
- evitar expressões como “comprovado”, “definitivo” ou “validado” sem evidência suficiente e verificável.

**Estado geral em 2026-10-22:** documentação consolidada; calibrações e auditorias reportadas; robustez do contraste espacial original enfraquecida pelo teste de bordas; validação independente dos dados e formulação de testes confirmatórios permanecem como prioridades.