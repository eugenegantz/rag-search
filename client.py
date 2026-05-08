#!/usr/bin/env python3
"""
HTTP-клиент к RAG Daemon
"""

import httpx
from typing import Any, Optional

from app_config.config import config
from core.paths import PORT_FILE

DAEMON_HOST = config["daemon"]["host"]
DAEMON_PORT = config["daemon"]["port"]


def get_daemon_url() -> Optional[str]:
    """Получить URL демона из файла порта."""
    if not PORT_FILE.exists():
        return None
    try:
        port = int(PORT_FILE.read_text().strip())
        return f"http://{DAEMON_HOST}:{port}"
    except (ValueError, OSError):
        return None


class RAGClient:
    """Клиент к RAG Daemon. Все операции -- быстрые HTTP-запросы."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or get_daemon_url()
        if not self.base_url:
            raise ConnectionError(
                "Демон не запущен. Запустите: python cli.py daemon start"
            )
        self.client = httpx.Client(base_url=self.base_url, timeout=120.0)

    def _post(self, path: str, json_data: dict[str, object]) -> dict[str, Any]:
        r = self.client.post(path, json=json_data)
        r.raise_for_status()
        return r.json()

    def _get(self, path: str) -> dict[str, Any]:
        r = self.client.get(path)
        r.raise_for_status()
        return r.json()

    def health(self) -> dict[str, Any]:
        return self._get("/api/health")

    def search(self, query: str, top_k: int = 10) -> dict[str, Any]:
        return self._post("/api/search", { "query": query, "top_k": top_k })

    def context(self, query: str, top_k: int = 10) -> dict[str, Any]:
        return self._post("/api/context/query", { "query": query, "top_k": top_k })

    def index(self, files: list[str], upsert: bool = True) -> dict[str, Any]:
        return self._post("/api/index/add", { "filepath": files })

    def files(self) -> dict[str, Any]:
        return self._get("/api/index/get")

    def remove(self, filepath: str) -> dict[str, Any]:
        return self._post("/api/index/remove", { "filepath": filepath })


def is_daemon_alive() -> bool:
    """Быстрая проверка, отвечает ли демон."""
    url = get_daemon_url()
    if not url:
        return False
    try:
        httpx.get(f"{url}/api/health", timeout=2.0).raise_for_status()
        return True
    except Exception:
        return False
