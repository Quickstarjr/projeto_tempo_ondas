# SPIA — demonstração de terminal real

Esta demo conecta uma página HTML a um Bash interativo real via PTY/WebSocket no WSL.

## 1. Instalar dependências no ambiente Python desejado

Ative o ambiente no WSL:
```bash
conda activate pta
```

Instale as dependências:
```bash
python -m pip install fastapi uvicorn
```

## 2. Iniciar

A partir desta pasta:
```bash
python server.py
```

Abra no navegador do Windows:
http://localhost:8765

O shell começa em `~/projeto_tempo_ondas` se essa pasta existir. Depois execute, na própria interface:
```bash
conda activate pta
cd ~/projeto_tempo_ondas
pwd
git status --short
```

## Observações importantes

- Esta é uma demo funcional mínima, não é ainda um terminal completo como xterm.js. Cores ANSI e alguns programas interativos podem não renderizar perfeitamente.
- O servidor aceita comandos reais com os privilégios do usuário Linux. Use apenas em sua própria máquina e mantenha-o limitado a `127.0.0.1`; não o exponha à rede.
- Cada conexão do navegador inicia uma sessão Bash própria. O ambiente ativado permanece nessa sessão enquanto a conexão ficar aberta.
- Não existe autenticação nesta demo; não a use em servidores públicos.
