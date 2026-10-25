#!/usr/bin/env python3
"""SPIA — terminal Bash via navegador. Uso exclusivamente local."""
from __future__ import annotations

import asyncio
import hashlib
import tempfile
import fcntl
import json
import os
import pty
import signal
import struct
import termios
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import HTTPException, Query
from fastapi.responses import FileResponse
import uvicorn

HERE = Path(__file__).resolve().parent
HTML = HERE / "terminal.html"
HOME = Path.home()
PROJECT = HOME / "projeto_tempo_ondas"

app = FastAPI()


@app.get("/")
async def index():
    return FileResponse(HTML)


MAX_READ_BYTES = 1_000_000
MAX_LIST_ITEMS = 500


def resolve_project_path(relative_path: str, *, must_exist: bool = True) -> Path:
    """Resolve um caminho sem permitir sair da raiz do projeto."""
    if "\x00" in relative_path:
        raise HTTPException(status_code=400, detail="Caminho inválido.")

    candidate = PROJECT / relative_path

    try:
        resolved = candidate.resolve(strict=must_exist)
        root = PROJECT.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        raise HTTPException(status_code=400, detail="Caminho inválido ou fora do projeto.")

    return resolved


@app.get("/api/files")
async def list_files(path: str = Query(default="")):
    """Lista um diretório do projeto; não segue links para fora da raiz."""
    directory = resolve_project_path(path)
    if not directory.is_dir():
        raise HTTPException(status_code=400, detail="O caminho não é um diretório.")

    items = []
    try:
        entries = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for entry in entries:
            # Ignora links simbólicos para evitar expor destinos externos.
            if entry.is_symlink():
                continue
            try:
                resolved = resolve_project_path(str(entry.relative_to(PROJECT)))
                if not (resolved.is_file() or resolved.is_dir()):
                    continue
                items.append({
                    "name": entry.name,
                    "path": str(entry.relative_to(PROJECT)),
                    "type": "directory" if resolved.is_dir() else "file",
                })
            except (HTTPException, OSError, RuntimeError):
                continue
            if len(items) >= MAX_LIST_ITEMS:
                break
    except OSError:
        raise HTTPException(status_code=400, detail="Não foi possível listar esse diretório.")

    return {"root": str(PROJECT), "path": path, "items": items}


@app.get("/api/file")
async def read_text_file(path: str = Query(..., min_length=1)):
    """Lê arquivos de texto pequenos e regulares dentro do projeto."""
    target = resolve_project_path(path)
    if target.is_symlink() or not target.is_file():
        raise HTTPException(status_code=400, detail="O caminho não é um arquivo regular.")

    try:
        if target.stat().st_size > MAX_READ_BYTES:
            raise HTTPException(status_code=413, detail="Arquivo maior que 1 MB.")
        data = target.read_bytes()
    except HTTPException:
        raise
    except OSError:
        raise HTTPException(status_code=400, detail="Não foi possível ler o arquivo.")

    if len(data) > MAX_READ_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo maior que 1 MB.")
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="Arquivo não é texto UTF-8.")

    return {"path": str(target.relative_to(PROJECT)), "content": content}


@app.get("/api/image")
async def read_image(path: str = Query(..., min_length=1)):
    """Entrega imagens para pré-visualização, limitadas à raiz do projeto."""
    target = resolve_project_path(path)
    if target.is_symlink() or not target.is_file():
        raise HTTPException(status_code=400, detail="O caminho não é um arquivo regular.")

    allowed_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = allowed_types.get(target.suffix.lower())
    if media_type is None:
        raise HTTPException(status_code=415, detail="Formato de imagem não suportado.")

    try:
        if target.stat().st_size > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Imagem maior que 20 MB.")
    except OSError:
        raise HTTPException(status_code=400, detail="Não foi possível acessar a imagem.")

    return FileResponse(
        target,
        media_type=media_type,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@app.post("/api/file")
async def save_text_file(payload: dict):
    """Salva texto UTF-8 se o arquivo não mudou desde a leitura."""
    relative_path = payload.get("path")
    content = payload.get("content")
    expected_sha256 = payload.get("expected_sha256")

    if not isinstance(relative_path, str) or not relative_path:
        raise HTTPException(status_code=400, detail="Caminho obrigatório.")
    if not isinstance(content, str):
        raise HTTPException(status_code=400, detail="O conteúdo deve ser texto.")
    if len(content.encode("utf-8")) > MAX_READ_BYTES:
        raise HTTPException(status_code=413, detail="Conteúdo maior que 1 MB.")
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        raise HTTPException(status_code=400, detail="Assinatura original obrigatória.")

    target = resolve_project_path(relative_path)
    if target.is_symlink() or not target.is_file():
        raise HTTPException(status_code=400, detail="Só é permitido salvar arquivos existentes e regulares.")

    try:
        original = target.read_bytes()
    except OSError:
        raise HTTPException(status_code=400, detail="Não foi possível ler o arquivo original.")

    current_sha256 = hashlib.sha256(original).hexdigest()
    if current_sha256 != expected_sha256:
        raise HTTPException(
            status_code=409,
            detail="O arquivo mudou desde a leitura. Reabra-o antes de salvar."
        )

    encoded = content.encode("utf-8")
    temp_name = None
    try:
        # Arquivo temporário no mesmo diretório para permitir substituição atômica.
        original_mode = target.stat().st_mode & 0o777
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=".spia-save-", delete=False
        ) as temp:
            temp_name = temp.name
            temp.write(encoded)
            temp.flush()
            os.fchmod(temp.fileno(), original_mode)
            os.fsync(temp.fileno())

        # Revalida o destino antes de substituir.
        checked = resolve_project_path(relative_path)
        if checked != target or target.is_symlink() or not target.is_file():
            raise HTTPException(status_code=409, detail="O destino mudou durante o salvamento.")

        # Confere novamente a versão imediatamente antes da substituição.
        latest = target.read_bytes()
        if hashlib.sha256(latest).hexdigest() != expected_sha256:
            raise HTTPException(status_code=409, detail="O arquivo mudou durante o salvamento.")

        os.replace(temp_name, target)
        temp_name = None
    except HTTPException:
        raise
    except OSError:
        raise HTTPException(status_code=400, detail="Falha ao salvar o arquivo.")
    finally:
        if temp_name:
            try:
                os.unlink(temp_name)
            except OSError:
                pass

    return {
        "path": str(target.relative_to(PROJECT)),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "saved": True,
    }


async def send_json(ws: WebSocket, payload: dict):
    await ws.send_text(json.dumps(payload, ensure_ascii=False))


def set_terminal_size(fd: int, rows: int, cols: int):
    rows = max(2, min(int(rows), 300))
    cols = max(2, min(int(cols), 500))
    size = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, size)


@app.websocket("/ws")
async def terminal_socket(ws: WebSocket):
    await ws.accept()

    pid, fd = pty.fork()

    if pid == 0:
        os.chdir(PROJECT if PROJECT.exists() else HOME)
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        os.execvpe("bash", ["bash", "--login", "-i"], env)

    loop = asyncio.get_running_loop()
    set_terminal_size(fd, 24, 80)

    async def reader():
        while True:
            try:
                data = await loop.run_in_executor(None, os.read, fd, 4096)
                if not data:
                    break
                await send_json(
                    ws,
                    {"type": "output", "data": data.decode("utf-8", errors="replace")},
                )
            except (OSError, WebSocketDisconnect):
                break

    async def writer():
        while True:
            message = await ws.receive_text()
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                continue

            kind = payload.get("type")

            if kind == "input":
                value = payload.get("data", "")
                if isinstance(value, str) and value:
                    os.write(fd, value.encode("utf-8"))

            elif kind == "resize":
                try:
                    set_terminal_size(fd, payload["rows"], payload["cols"])
                    os.kill(pid, signal.SIGWINCH)
                except (KeyError, ValueError, TypeError, OSError):
                    pass

    tasks = [
        asyncio.create_task(reader()),
        asyncio.create_task(writer()),
    ]

    try:
        await send_json(ws, {"type": "status", "text": "Bash conectado"})
        _, pending = await asyncio.wait(
            tasks, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            os.close(fd)
        except OSError:
            pass


if __name__ == "__main__":
    print("SPIA — http://127.0.0.1:8765")
    print("Terminal local: não exponha esta porta à rede.")
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
