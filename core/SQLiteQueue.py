import json
import typing
import sqlite3
import threading

from datetime import datetime
from pathlib import Path as _Path

class SQLiteQueue:
    """Очередь задач в SQLite. Блокирует на get() если очередь пуста."""

    def __init__(
        self,
        db_path: _Path,
        task_registry: dict[str, typing.Callable[..., typing.Any]],
    ):
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._task_registry = task_registry
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_table()


    def _ensure_table(self):
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    method VARCHAR(128) NOT NULL,
                    cdate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    args DEFAULT '[]'
                )
            """)


    def put(self, task_name: str, args: list[typing.Any]):
        """Добавить задачу в очередь."""
        with self._lock:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO queue (method, cdate, args) VALUES (?, ?, ?)",
                    (task_name, datetime.now().isoformat(), json.dumps(args, ensure_ascii=False))
                )
            self._not_empty.notify()


    def get(self) -> tuple[typing.Callable[..., typing.Any], list[typing.Any]]:
        """Извлечь первую задачу (блокирует если пусто) и удалить из БД."""
        with self._not_empty:
            while True:
                row = self._conn.execute(
                    "SELECT id, method, args FROM queue ORDER BY id ASC LIMIT 1"
                ).fetchone()
                if row:
                    break
                self._not_empty.wait()

            task_id = row["id"]
            task_name = row["method"]
            args = json.loads(row["args"]) if row["args"] else []

            with self._conn:
                self._conn.execute("DELETE FROM queue WHERE id = ?", (task_id,))

        func = self._task_registry[task_name]
        return func, args


    def peek_all(self) -> list[dict[str, typing.Any]]:
        """Вернуть копию всех задач без удаления."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, method, cdate, args FROM queue ORDER BY id ASC"
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "task": row["method"],
                    "cdate": row["cdate"],
                    "args": json.loads(row["args"]) if row["args"] else [],
                }
                for row in rows
            ]


    def __len__(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) as cnt FROM queue").fetchone()
            return row["cnt"] if row else 0