
---

### 2. `CHANGELOG.md`
## [Não lançado] - 2026-10-20

### Adicionado
- **Análise Estelar:** Criação do kit de experimentos para a estrela KIC 757450 usando `lightkurve` (curva de luz, Lomb-Scargle e BLS).
- **Análise de Galáxias:** Download de ~8.000 galáxias do SDSS (SpecPhoto) e análise de espectro de potência.
- **Teste de Chladni Cósmico:** Experimento de segregação de massa (`galaxias_tamanho.py`), confirmando visualmente os filamentos (nós) e vazios (ventres) com galáxias massivas e anãs.
- **Documentação de Ambiente:** Criação do `ambiente_v2.md` contendo todas as bibliotecas de astronomia, GPU e limitações do MCMC.
- **Nomenclatura Formal:** Renomeação dos arquivos de membros do grupo (`DeepSeek.md`, `Google_Gemini.md`, `OpenAI_GPT.md`, `xAI_Grok.md`).

### Corrigido
- **SDSS Redshift:** Correção do bug de sobrescrita da coluna `z` no script de galáxias.
- **Filtro de Dados:** Adição do filtro `modelMag_r > 0` para ignorar dados ausentes (`-9999.0`) no SDSS.
```markdown
# CHANGELOG — Projeto Tempo, Ondas e Observador

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/)
Versionamento: informal, por versão de arquivo de continuidade.

---

## [V5.2] — 2026-10-16

### Adicionado
- Definições operacionais expandidas (§1.5, formas funcionais).
- §1.3 com três cenários de ordem de grandeza para frequência.
- §8.1 com critérios de falsificação por hipótese.
- §9.3 com ressalva sobre limitações dos PTAs.
- §9.4 com protocolo de pré-registro.
- Arquivo separado `gaveta_filosofica_v1.txt`.
- Pipeline `pipeline_v2.py` (modos diagnóstico, sanidade, anisotropia).
- README de pré-registro.
- Registro de testes 2026-10-16.

### Alterado
- Material filosófico movido para arquivo externo.
- Referência cruzada entre V5.2 e gaveta estabelecida.

### Validação
- 3 modos do pipeline passaram em dados sintéticos.
- Bug de Windows/Python 3.14 em savefig corrigido.

---

## [V5.1] — 2026-10-16

### Adicionado
- Refinamentos técnicos do Gemini (PTAs, Shklovskii, Euler, DTM).
- Page–Wootters explicitado (§3.5).
- Hipóteses 18 e 19.

### Alterado
- Teste com resíduos de PTAs substituiu pulsares isolados.

---

## [V5.0] — 2026-10-16

### Adicionado
- Definições operacionais (§1).
- Quatro leituras de "onda" separadas.

---

## [V4] — 2026-10-16

### Adicionado
- Gaveta filosófica isolada.
- Tabela de hipóteses com status.

---

## [V3 e anteriores] — 2026-10-16

- Versões preliminares com imagem mental do cubo e das duas ondas.