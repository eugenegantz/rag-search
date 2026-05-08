#!/usr/bin/env python3
"""
RAG Daemon -- единый backend.
Раздает статику, API для веба и CLI.
Модели загружаются один раз при старте.
"""

import os
import queue
import typing
import uvicorn

import threading

from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app_config.config import config
from core.paths import PORT_FILE, PID_FILE

# import core.deps as deps
from core.deps.default_logger import default_logger as logger
from core.deps.resource_indexer import resource_indexer as _indexer
from core.deps.rag_search import rag

# --- Настройки ---
DAEMON_HOST = config["daemon"]["host"]
DAEMON_PORT = config["daemon"]["port"]

# Фоновая очередь индексации
background_queue: queue.Queue[
    tuple[
        typing.Callable[..., typing.Any],
        list[typing.Any]
    ]
] = queue.Queue()

def background_worker():
    while True:
        func, args = background_queue.get()
        logger.info({ "event": "background-worker-task", "args": args, "datetime": str(datetime.now()) })
        try:
            func(*args)
        except Exception as e:
            logger.error({ "event": "background-worker-error", "error": e, "datetime": str(datetime.now()) })
        finally:
            background_queue.task_done()

worker_thread = threading.Thread(target=background_worker, daemon=True)
worker_thread.start()


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


@handleErrorDecorator
@app.post("/api/search")
def api_search(req: SearchRequest):
    """RAG-поиск по индексированным документам."""
    res = rag.search(req.query, n_results=req.top_k or 10)

    return {
        "results": [res]
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
        background_queue.put((
            _indexer.upsert_file_to_index,
            [filepath]
        ))

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
@app.post("/api/index/remove")
def api_remove(req: RemoveRequest):
    """Удалить файл из индекса."""
    assert _indexer is not None
    _indexer.remove_from_index(req.filepath)
    return { "message": "Удалено" }


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
