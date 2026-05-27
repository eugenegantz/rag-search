#!/usr/bin/env python3
"""
RAG Daemon -- единый backend.
Раздает статику, API для веба и CLI.
Модели загружаются один раз при старте.
"""

import os
import json
import typing
import uvicorn
import sqlite3

import threading

from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path as _Path

from app_config.config import config
from core.paths import PORT_FILE, PID_FILE, DB_FILE
from core.SQLiteQueue import SQLiteQueue

# import core.deps as deps
from core.deps.default_logger import default_logger as logger
from core.deps.resource_indexer import resource_indexer as _indexer
from core.deps.rag_search import rag

# --- Настройки ---
DAEMON_HOST = config["daemon"]["host"]
DAEMON_PORT = config["daemon"]["port"]

_uvicorn_server: uvicorn.Server | None = None

# --- Очередь ---

TASK_REGISTRY: dict[str, typing.Callable[..., typing.Any]] = {
    "upsert_file_to_index": _indexer.upsert_file_to_index,
}

# Фоновая очередь индексации
background_queue = SQLiteQueue(DB_FILE, TASK_REGISTRY)

queue_running = threading.Event()
queue_running.clear()

def background_worker():
    while True:
        # Если флаг сброшен, поток заблокируется здесь и будет ждать .set()
        queue_running.wait()

        func, args = background_queue.get()
        logger.info({ "event": "background-worker-task", "args": args, "datetime": str(datetime.now()) })

        try:
            func(*args)
        except Exception as e:
            logger.error({ "event": "background-worker-error", "error": e, "datetime": str(datetime.now()) })

# Как управлять:
# queue_running.clear()  -- Поставить на паузу (текущая задача доделается, новые не возьмутся)
# queue_running.set()    -- Снять с паузы

worker_thread = threading.Thread(target=background_worker, daemon=True)
worker_thread.start()

# ------------------

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     pass


app = FastAPI(
    title="RAG Daemon",
    version="1.0.0",
    # lifespan=lifespan,
)

# Раздача статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Pydantic схемы ---

class SearchRequest(BaseModel):
    query: str
    top_k: typing.Optional[int] = 10
    rtype: typing.Optional[str] = ""


class IndexRequest(BaseModel):
    files: list[str]
    upsert: bool = True


class TAPIIndexAddReq(BaseModel):
    filepath: list[str]


class RemoveRequest(BaseModel):
    filepath: str


# --- Frontend routes ---

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/add")
def read_add():
    return FileResponse("static/add.html")

@app.get("/search-files")
def read_search_files():
    return FileResponse("static/search-files.html")


# --- API endpoints ---

def handleErrorDecorator(
    func: typing.Callable[
        ...,
        typing.Any
    ]
) -> typing.Callable[..., dict[str, object]]:
    def _wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        try:
            res = func(*args, **kwargs)
            res["error"] = ""
            return res
        except Exception as err:
            return {
                "error": str(err),
                "content": "",
                "refs": [], # type: ignore
            }
    return _wrapper


@handleErrorDecorator
@app.get("/api/health")
def health():
    # TODO: проверять состояние службы
    return {
        "status": "ok",
        "backend_ready": "ok",
    }


@app.post("/api/shutdown")
def shutdown():
    """Graceful shutdown демона."""
    def _stop():
        if _uvicorn_server is not None:
            _uvicorn_server.should_exit = True

    threading.Thread(target=_stop, daemon=True).start()
    return {"status": "shutting_down"}


@handleErrorDecorator
@app.post("/api/search")
def api_search(req: SearchRequest):
    """RAG-поиск по индексированным документам."""
    results = rag.search(req.query, n_results=req.top_k or 10)

    return {
        "results": results
    }


@handleErrorDecorator
@app.post("/api/context/query")
def api_context(req: SearchRequest):
    """Сырой поиск чанков (без LLM)."""
    ctx = rag.fetch_context(req.query, n_results=req.top_k or 10)
    return {
        "context": ctx
    }


@handleErrorDecorator
@app.post("/api/index/query")
def api_index_query(req: SearchRequest):
    """Сырой поиск по файлам (без LLM)."""
    meta = rag.search_meta(
        query=req.query,
        n_results=req.top_k or 10,
        rtype=req.rtype or "",
    )
    return {
        "meta": meta
    }


@handleErrorDecorator
@app.post("/api/index/add")
async def api_index_add(request: TAPIIndexAddReq):
    """Добавление документа в индекс (веб). С фоновой очередью."""
    # Валидация пути
    errors: list[str] = []

    for filepath in request.filepath:
        is_valid, error_msg = _indexer.validate_file_path(filepath)
        if not is_valid:
            errors.append(error_msg)

    if errors:
        return { "error": ";\n".join(errors) }

    # Фоновая индексация
    for filepath in request.filepath:
        logger.info({ "event": "background-queue-put", "args": [filepath], "datetime": str(datetime.now()) })
        background_queue.put("upsert_file_to_index", [filepath])

    return {
        "error": "",
        "message": "Документ поставлен в очередь на индексацию",
    }


@handleErrorDecorator
@app.get("/api/index/get")
def api_index_get():
    """Вернуть список файлов в индексе."""
    assert _indexer is not None
    return {
        "filepaths": _indexer.list_indexed_files(),
    }


@handleErrorDecorator
@app.post("/api/index/queue/pause")
def api_index_queue_pause():
    """Приостановить обработку очереди"""
    try:
        queue_running.clear()
        return { "error": "" }

    except Exception as err:
        return { "error": str(err) }


@handleErrorDecorator
@app.post("/api/index/queue/unpause")
def api_index_queue_unpause():
    """Возобновить обработку очереди"""
    try:
        queue_running.set()
        return { "error": "" }

    except Exception as err:
        return { "error": str(err) }


@handleErrorDecorator
@app.post("/api/index/queue/get")
def api_index_queue_get():
    """Получить содержимое очереди без изменения"""
    items = background_queue.peek_all()
    queue_list = [str(item["args"][0]) for item in items]

    return {
        "queue": queue_list
    }


@handleErrorDecorator
@app.get("/api/index/queue/status")
def api_index_queue_status():
    """Получить статус очереди (paused/active)"""
    return {
        "paused": not queue_running.is_set(),
    }


@handleErrorDecorator
@app.post("/api/index/remove")
def api_remove(req: RemoveRequest):
    """Удалить файл из индекса."""
    assert _indexer is not None
    _indexer.remove_from_index(req.filepath)
    return { "message": "Удалено" }


@app.get("/files/{filepath:path}")
def static_files_get(filepath: str):
    """Получить файл из индекса."""

    print('test test test')

    ext = _Path(filepath).suffix.lower()

    p = _Path(filepath)

    if not p.exists():
        raise HTTPException(status_code=404, detail="Файл не существует на диске")

    media_types = {
        ".jpeg": "image/jpeg",
        ".jpg": "image/jpeg",
        ".png": "image/png",
    }

    return FileResponse(filepath, media_type=media_types.get(ext, "application/octet-stream"))


# --- Точка входа ---

def start_daemon(
    host: str | None = None,
    port: int | None = None
):
    """Запуск uvicorn программно."""
    host = host or DAEMON_HOST
    port = port or DAEMON_PORT

    cfg = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(cfg)

    global _uvicorn_server
    _uvicorn_server = server

    # Сохраняем PID и порт для CLI-клиента
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))
    PORT_FILE.write_text(str(port))

    try:
        server.run()
    finally:
        PID_FILE.unlink(missing_ok=True)
        PORT_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    start_daemon()
