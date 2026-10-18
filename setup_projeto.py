"""
setup_projeto.py — Cria a estrutura de pastas do projeto.

Uso:
    python setup_projeto.py

Cria todas as pastas necessárias e arquivos .gitkeep onde
necessário. Seguro de rodar múltiplas vezes: não sobrescreve
arquivos existentes.
"""

from pathlib import Path

RAIZ = Path(__file__).parent.resolve()

PASTAS = [
    'docs',
    'src',
    'src/utils',
    'data',
    'data/synthetic',
    'data/raw',
    'data/processed',
    'outputs',
    'outputs/plots',
    'outputs/reports',
    'notebooks',
    'tests',
    'scripts',
    'web',
    'web/templates',
    'web/static',
    'db',
    'db/migrations',
]

def criar_estrutura():
    print(f"Raiz do projeto: {RAIZ}\n")
    for pasta in PASTAS:
        caminho = RAIZ / pasta
        caminho.mkdir(parents=True, exist_ok=True)
        gitkeep = caminho / '.gitkeep'
        if not gitkeep.exists():
            gitkeep.touch()
        print(f"[+] {caminho.relative_to(RAIZ)}")
    print("\nEstrutura criada com sucesso.")
    print("Próximo passo: mover seus arquivos para as pastas respectivas.")

if __name__ == '__main__':
    criar_estrutura()