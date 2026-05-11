import os
import re
import uuid
import logging
import typing
from core.types import TCDBMetaEntry
from datetime import datetime
from pathlib import Path

from core.readers.ChunkReaderFactory import ChunkReaderFactory
from core.consts import ALLOWED_EXTENSIONS

class ResourceIndexer:
    """Индексатор документов в ChromaDB."""

    def __init__(
        self,
        db: typing.Any,
        pipe: typing.Any,
        name: str,
        logger: logging.Logger | None = None,
    ):
        """
        Args:
            db: chromadb.PersistentClient instance
            pipe: transformers pipeline("feature-extraction")
            name: имя коллекции в ChromaDB
        """
        self.db = db
        self.pipe = pipe
        self.logger = logger
        self.name = name
        self.collection = db.get_or_create_collection(name=name)


    def unify_path(self, path: str) -> str:
        """Привести пути к единому виду"""

        path = path.strip()
        if self.is_web_url(path):
            return path
        return os.path.abspath(os.path.normpath(path))


    def is_web_url(self, url: str) -> bool:
        url = url.strip()

        if re.findall(r'^http(s?):', url, re.I):
            return True
        else:
            return False


    def validate_file_path(self, filepath: str) -> tuple[bool, str]:
        """Проверяет путь к файлу на валидность."""

        path = Path(filepath)

        if self.is_web_url(str(filepath)):
            return True, ""

        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            return False, f"Неподдерживаемый формат: {path.suffix}"
        
        if not path.exists():
            return False, f"Файл не найден: {filepath}"

        if not path.is_file():
            return False, f"Не файл: {filepath}"

        return True, ""


    def add_file_to_index(self, filepath: str) -> None:
        """Добавить файл в индекс (создаёт новые записи)."""

        filepath = self.unify_path(filepath)
        reader = ChunkReaderFactory.get_reader(filepath)
        chunks = reader.createChunksIterator()
        chunks_length = 0

        for chunk in chunks:
            chunks_length += 1
            emb = self.pipe(chunk["text"])[0][0]
            _id = str(uuid.uuid4())

            self.collection.add(
                ids=[_id],
                embeddings=[emb],
                documents=[filepath],
                metadatas=[{
                    "filepath": filepath,
                    "from": chunk["from"],
                    "to": chunk["to"],
                }],
            )

        if self.logger:
            self.logger.info({
                "event": "file-added-to-index",
                "target": "ResourceIndexer",
                "filepath": filepath,
                "chunks.length": chunks_length,
                "datetime": str(datetime.now()),
            })


    def upsert_file_to_index(self, filepath: str) -> None:
        """Обновить файл в индексе (удалить старое + добавить новое)."""

        filepath = self.unify_path(filepath)

        self.collection.delete(where={"filepath": filepath})
        self.add_file_to_index(filepath)


    def list_indexed_files(self) -> list[str]:
        """Получить список всех файлов в индексе."""

        results = self.collection.get()
        metas: list[TCDBMetaEntry] = results["metadatas"] or []
        files = {meta.get("filepath", "") for meta in metas if meta.get("filepath")}

        return sorted(files)


    def remove_from_index(self, filepath: str) -> None:
        """Удалить файл из индекса."""

        filepath = self.unify_path(filepath)

        self.collection.delete(where={"filepath": filepath})

        if self.logger:
            self.logger.info({
                "event": "file-removed-from-index",
                "target": "ResourceIndexer",
                "filepath": filepath,
                "datetime": str(datetime.now()),
            })
