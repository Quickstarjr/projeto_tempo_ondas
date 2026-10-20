# Experimento: galaxias_tda

![diagrama_persistencia.png](https://raw.githubusercontent.com/Quickstarjr/projeto_tempo_ondas/main/outputs/reports/galaxias_tda/diagrama_persistencia.png)

![curva_betti.png](https://raw.githubusercontent.com/Quickstarjr/projeto_tempo_ondas/main/outputs/reports/galaxias_tda/curva_betti.png)


## Análise Topológica de Dados (TDA)
Este experimento aplicou Homologia Persistente nos dados do SDSS para quantificar a estrutura da teia cósmica.
O **Diagrama de Persistência** mostra quais estruturas sobrevivem ao longo das escalas (pontos longe da diagonal).
A **Curva de Betti H1** conta quantos anéis topológicos existem em cada escala. Se a Grande Onda estiver estruturada como as Figuras de Chladni, devemos ver picos claros nesta curva.

### Próximos passos:
Comparar esta curva com um catálogo de pontos aleatórios (Monte Carlo) para provar que a estrutura não é ruído.
## Análise Metodológica (Resultado Nulo e Limitações)

A aplicação da Homologia Persistente (TDA) em 8.000 galáxias do SDSS (projeção 2D e 3D) resultou em um pico de H1 de apenas 253 anéis na escala de 3.0 Mpc, morrendo rapidamente em escalas maiores.

### Interpretação
O resultado é **nulo** para a detecção de grandes anéis cósmicos (> 50 Mpc). A causa não é falha no código ou no `ripser`, mas sim a **esparsidade da amostra**. Com 8.000 galáxias espalhadas em um volume de 300x300x200 Mpc, a distância média entre vizinhas (~3-5 Mpc) impede que o algoritmo conecte os pontos para formar estruturas contínuas de larga escala.

### Lição Metodológica
O olho humano (que desenhou os filamentos visualmente) faz uma interpolação natural que a TDA estrita não faz. Para a próxima fase, será necessário aplicar um campo de densidade contínuo (KDE - Kernel Density Estimation) ou usar amostras de milhões de galáxias para que a TDA revele a verdadeira topologia da Cosmic Web.