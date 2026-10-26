#!/usr/bin/env python3
"""Biblioteca local do Filhote. Não envia dados à rede."""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
INDEX = HERE / "indice.json"

MAX_INDEX_FILE = 1_000_000
MAX_READ_FILE = 200_000
MAX_INDEXED_FILES = 20_000
MAX_SEARCH_RESULTS = 12

TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".html", ".css", ".js", ".json",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".sh", ".bat",
    ".csv", ".tsv", ".sql", ".xml", ".rst", ".ipynb",
}
SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache",
    ".idea", ".vscode", "site-packages",
}
SKIP_NAMES = {
    ".env", ".env.local", ".env.production",
}
SKIP_SUFFIXES = {
    ".pyc", ".pyo", ".bak", ".log", ".pid",
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".pdf", ".zip", ".gz", ".parquet", ".fits",
    ".sqlite", ".db", ".exe", ".dll", ".so",
}
SECRET_PATTERNS = (
    "*.pem", "*.key", "*secret*", "*credential*",
    "*token*", "*password*", "*passwd*",
)
SECRET_TEXT_PATTERNS = (
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\bsk-[A-Za-z0-9_-]{20,}\b",
    r"\bNVIDIA_API_KEY\s*=",
    r"\b(?:OPENAI|ANTHROPIC|AWS|GITHUB|HF|HUGGINGFACE)_"
    r"(?:API_KEY|ACCESS_KEY|SECRET_KEY|TOKEN)\s*[:=]",
    r"\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|"
    r"password|passwd|secret)\s*[:=]\s*['\"]?[^\s'\"]{8,}",
    r"\bgh[pousr]_[A-Za-z0-9]{20,}\b",
    r"\bAKIA[A-Z0-9]{16}\b",
)

def rel(path: Path) -> str:
    return path.relative_to(PROJECT).as_posix()

def safe_path(relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise ValueError("Caminho inválido.")
    target = (PROJECT / relative).resolve(strict=True)
    target.relative_to(PROJECT.resolve(strict=True))
    if target.is_symlink() or not target.is_file():
        raise ValueError("O caminho não é um arquivo regular.")
    if any(part in SKIP_DIRS for part in Path(relative).parts):
        raise ValueError("Diretório excluído da biblioteca.")
    if is_excluded(target):
        raise ValueError("Arquivo excluído da biblioteca.")
    return target

def is_excluded(path: Path) -> bool:
    name = path.name.lower()
    # O índice é gerado pela própria biblioteca; não deve catalogar a si mesmo.
    if name == INDEX.name.lower() and path.parent.resolve() == HERE.resolve():
        return True
    if name in SKIP_NAMES or name.startswith(".env."):
        return True
    if name.endswith(tuple(s.lower() for s in SKIP_SUFFIXES)):
        return True
    if name.startswith(("server.py.backup-", "terminal.html.backup-")):
        return True
    if name.endswith((".bak", ".bak-", ".pre_correcao")):
        return True
    if any(fnmatch.fnmatch(name, p) for p in SECRET_PATTERNS):
        return True
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    return False

def text_is_safe(text: str) -> bool:
    return not any(re.search(p, text, flags=re.IGNORECASE)
                   for p in SECRET_TEXT_PATTERNS)

def read_small_text(path: Path, limit: int) -> str:
    if path.stat().st_size > limit:
        raise ValueError("Arquivo maior que o limite de leitura.")
    data = path.read_bytes()
    if len(data) > limit:
        raise ValueError("Arquivo excedeu o limite durante a leitura.")
    text = data.decode("utf-8")
    if "\x00" in text:
        raise ValueError("Arquivo parece binário.")
    if not text_is_safe(text):
        raise ValueError("Conteúdo contém padrão de credencial; leitura bloqueada.")
    return text

def make_entry(path: Path) -> dict | None:
    if path.is_symlink() or not path.is_file() or is_excluded(path):
        return None
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return None
    try:
        size = path.stat().st_size
        entry = {
            "path": rel(path),
            "type": path.suffix.lower().lstrip("."),
            "bytes": size,
            "modified": datetime.fromtimestamp(
                path.stat().st_mtime, timezone.utc
            ).isoformat(),
            "indexed_content": False,
            "summary": "",
        }
        # CSVs grandes ficam catalogados por metadados; não são ingeridos.
        if size <= MAX_INDEX_FILE:
            try:
                text = read_small_text(path, MAX_INDEX_FILE)
                # Não guardar resumo de arquivos de configuração ou ambiente.
                if path.name.lower().startswith((".env", "config", "settings")):
                    entry["summary"] = "Arquivo de configuração; conteúdo não resumido."
                    entry["indexed_content"] = False
                elif path.suffix.lower() == ".csv":
                    entry["summary"] = "Cabeçalho CSV: " + (
                        text.splitlines()[0][:500] if text.splitlines() else "(vazio)"
                    )
                elif path.suffix.lower() == ".ipynb":
                    obj = json.loads(text)
                    cells = obj.get("cells", [])
                    bits = []
                    for cell in cells[:12]:
                        source = cell.get("source", "")
                        if isinstance(source, list):
                            source = "".join(source)
                        if cell.get("cell_type") == "markdown":
                            bits.append(source)
                    entry["summary"] = " ".join(bits)[:700]
                else:
                    # Pequeno resumo para busca; conteúdo integral não fica no índice.
                    lines = [line.strip() for line in text.splitlines()
                             if line.strip() and not line.lstrip().startswith("#!")]
                    entry["summary"] = " ".join(lines[:4])[:700]
                if not path.name.lower().startswith((".env", "config", "settings")):
                    entry["indexed_content"] = True
            except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
                entry["summary"] = "Metadados apenas; conteúdo não indexado."
        else:
            entry["summary"] = "Arquivo grande; metadados apenas."
        return entry
    except OSError:
        return None

def index_project() -> dict:
    entries = []
    for base, dirs, files in os.walk(PROJECT, followlinks=False):
        base_path = Path(base)
        dirs[:] = sorted(
            d for d in dirs
            if d not in SKIP_DIRS and not (base_path / d).is_symlink()
        )
        for filename in sorted(files):
            path = base_path / filename
            entry = make_entry(path)
            if entry is not None:
                entries.append(entry)
                if len(entries) >= MAX_INDEXED_FILES:
                    break
        if len(entries) >= MAX_INDEXED_FILES:
            break

    entries.sort(key=lambda item: item["path"].lower())
    result = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT),
        "file_count": len(entries),
        "policy": {
            "network_access": False,
            "max_file_bytes_for_content_index": MAX_INDEX_FILE,
            "max_file_bytes_for_read": MAX_READ_FILE,
            "excluded": sorted(SKIP_DIRS),
            "content_is_stored": False,
        },
        "files": entries,
    }
    tmp = INDEX.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    os.replace(tmp, INDEX)
    return result

def load_index() -> dict:
    if not INDEX.is_file():
        raise RuntimeError("Índice inexistente. Execute 'indexar' primeiro.")
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("files"), list):
        raise RuntimeError("Formato de índice inválido.")
    return data


# Limites exclusivos da busca em fluxo; a leitura normal permanece limitada.
MAX_SEARCH_FILE_BYTES = 25 * 1024 * 1024
MAX_SEARCH_TOTAL_BYTES = 250 * 1024 * 1024
SEARCH_CHUNK_BYTES = 64 * 1024
MAX_SEARCH_LINE_BYTES = 1024 * 1024


def _search_stream_file(path: Path, pattern) -> tuple[int, list[dict]]:
    """Busca por linhas em blocos; só devolve trechos após validar o arquivo inteiro."""
    occurrences = 0
    excerpts = []
    line_number = 0
    pending = bytearray()
    total_bytes = 0

    with path.open("rb") as stream:
        while True:
            chunk = stream.read(SEARCH_CHUNK_BYTES)
            if not chunk:
                break

            total_bytes += len(chunk)
            if total_bytes > MAX_SEARCH_FILE_BYTES:
                raise ValueError("Arquivo excedeu o limite de busca em fluxo.")

            pending.extend(chunk)

            while True:
                newline = pending.find(b"\n")
                if newline < 0:
                    break

                raw_line = bytes(pending[:newline])
                del pending[:newline + 1]
                line_number += 1

                if len(raw_line) > MAX_SEARCH_LINE_BYTES:
                    raise ValueError("Linha excedeu o limite seguro de busca.")

                line = raw_line.decode("utf-8")
                if not text_is_safe(line):
                    raise ValueError(
                        "Conteúdo contém padrão de credencial; leitura bloqueada."
                    )

                found = list(pattern.finditer(line))
                if found:
                    occurrences += len(found)
                    if len(excerpts) < 5:
                        excerpts.append({
                            "line": line_number,
                            "text": line.strip()[:500],
                        })

            if len(pending) > MAX_SEARCH_LINE_BYTES:
                raise ValueError("Linha excedeu o limite seguro de busca.")

        if pending:
            line_number += 1
            line = bytes(pending).decode("utf-8")
            if not text_is_safe(line):
                raise ValueError(
                    "Conteúdo contém padrão de credencial; leitura bloqueada."
                )
            found = list(pattern.finditer(line))
            if found:
                occurrences += len(found)
                if len(excerpts) < 5:
                    excerpts.append({
                        "line": line_number,
                        "text": line.strip()[:500],
                    })

    return occurrences, excerpts


def search_literal(
    query: str, limit: int = MAX_SEARCH_RESULTS
) -> tuple[list[dict], dict]:
    """Busca literal em texto permitido; arquivos grandes são lidos em fluxo."""
    query = query.strip()
    empty_stats = {
        "scanned": 0, "skipped": 0, "matched_files": 0,
        "bytes_scanned": 0,
    }
    if not query or len(query) > 300:
        return [], empty_stats

    single_word = re.fullmatch(r"\w+", query, flags=re.UNICODE) is not None
    pattern = (
        re.compile(r"(?<!\w)" + re.escape(query) + r"(?!\w)", re.IGNORECASE)
        if single_word else re.compile(re.escape(query), re.IGNORECASE)
    )

    results = []
    scanned = 0
    skipped = 0
    bytes_scanned = 0

    # Primeiro percorre arquivos menores em TODO o projeto.
    # Assim, arquivos enormes não consomem o orçamento antes dos documentos.
    entries = sorted(
        load_index()["files"],
        key=lambda entry: (
            int(entry.get("bytes") or 0) > MAX_READ_FILE,
            int(entry.get("bytes") or 0),
            str(entry.get("path") or "").lower(),
        ),
    )

    for entry in entries:
        relative = entry.get("path", "")
        try:
            path = safe_path(relative)
            suffix = path.suffix.lower()

            if suffix not in TEXT_EXTENSIONS:
                skipped += 1
                continue

            size = path.stat().st_size
            if size > MAX_SEARCH_FILE_BYTES:
                skipped += 1
                continue
            if bytes_scanned + size > MAX_SEARCH_TOTAL_BYTES:
                skipped += 1
                continue

            if size <= MAX_READ_FILE:
                text = read_small_text(path, MAX_READ_FILE)
                occurrences = 0
                excerpts = []
                for line_number, line in enumerate(text.splitlines(), start=1):
                    found = list(pattern.finditer(line))
                    if found:
                        occurrences += len(found)
                        if len(excerpts) < 5:
                            excerpts.append({
                                "line": line_number,
                                "text": line.strip()[:500],
                            })
                bytes_scanned += size
            elif suffix in {".txt", ".csv"}:
                occurrences, excerpts = _search_stream_file(path, pattern)
                bytes_scanned += size
            else:
                skipped += 1
                continue

            scanned += 1

            if occurrences:
                results.append({
                    "path": relative,
                    "bytes": size,
                    "type": entry.get("type"),
                    "score": occurrences,
                    "summary": entry.get("summary", ""),
                    "matches": excerpts,
                })

        except (OSError, ValueError, UnicodeError):
            # Não divulgar trechos parciais de arquivos que falhem na validação.
            skipped += 1
            continue

    results.sort(key=lambda item: (-item["score"], item["path"].lower()))
    stats = {
        "scanned": scanned,
        "skipped": skipped,
        "matched_files": len(results),
        "bytes_scanned": bytes_scanned,
    }
    return results[:max(1, min(limit, 30))], stats

def search_index(query: str, limit: int = MAX_SEARCH_RESULTS) -> list[dict]:
    """Compatibilidade com a interface existente; busca literal por padrão."""
    results, _ = search_literal(query, limit)
    return results

def read_file(relative: str) -> dict:
    path = safe_path(relative)
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        raise ValueError("Formato não autorizado para leitura.")
    text = read_small_text(path, MAX_READ_FILE)
    return {
        "path": rel(path),
        "bytes": path.stat().st_size,
        "content": text,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("indexar", help="Gera o índice local de arquivos permitidos")
    search = sub.add_parser("buscar", help="Busca por nome e resumo")
    search.add_argument("consulta")
    search.add_argument("--limite", type=int, default=MAX_SEARCH_RESULTS)
    read = sub.add_parser("ler", help="Lê um arquivo de texto permitido")
    read.add_argument("caminho")
    args = parser.parse_args()

    try:
        if args.command == "indexar":
            data = index_project()
            print(f"Índice criado: {INDEX.relative_to(PROJECT)}")
            print(f"Arquivos catalogados: {data['file_count']}")
            print("Conteúdos enviados à rede: nenhum")
        elif args.command == "buscar":
            results, stats = search_literal(args.consulta, args.limite)
            print(f"Consulta literal: {args.consulta!r}")
            print(
                f"Arquivos examinados: {stats['scanned']} | "
                f"Ignorados/bloqueados: {stats['skipped']} | "
                f"Bytes examinados: {stats['bytes_scanned']:,} | "
                f"Arquivos com ocorrências: {stats['matched_files']}"
            )

            if not results:
                print("Nenhuma ocorrência encontrada no conjunto examinado.")

            for item in results:
                print(
                    f"\n[{item['score']} ocorrência(s)] {item['path']} "
                    f"({item['bytes']} bytes)"
                )
                for match in item.get("matches", []):
                    print(f"    Linha {match['line']}: {match['text']}")
        elif args.command == "ler":
            item = read_file(args.caminho)
            print(f"FONTE: {item['path']}")
            print(f"TAMANHO: {item['bytes']} bytes\n")
            print(item["content"])
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERRO: {exc}")
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
