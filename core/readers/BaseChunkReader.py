import typing
from abc import ABC, abstractmethod
from core.types import TChunk, TChunkArgs



class BaseChunkReader(ABC):
    """Базовый класс для чтения чанков из файлов различных форматов."""

    @abstractmethod
    def getChunk(self, from_: list[int], to: list[int]) -> TChunk:
        """Прочитать и вернуть указанный чанк текста по координатам from/to."""
        pass


    @abstractmethod
    def createChunks(self) -> list[TChunk]:
        """Создать и вернуть все чанки (логика chunking по предложениям)."""
        pass


    @abstractmethod
    def createChunksIterator(self) -> typing.Iterator[TChunk]:
        """Создать и вернуть все чанки (логика chunking по предложениям)."""
        pass


    @abstractmethod
    def load(self) -> None:
        """Загрузить данные из источника."""
        pass


    @abstractmethod
    def is_loaded(self) -> bool:
        """Возвращает True, если данные уже загружены."""
        pass


    def getChunks(self, chunks_meta: list[TChunkArgs]) -> list[TChunk]:
        """
        Принять список чанков с координатами from/to,
        объединить перекрывающиеся диапазоны и вернуть чанки без дублей.
        """
        if not chunks_meta:
            return []

        # Сортировать по координатам from (лексикографическая)
        sorted_meta = sorted(chunks_meta, key=lambda x: x["from"])

        merged: list[TChunkArgs]    = []
        current_from                = sorted_meta[0]["from"]
        current_to                  = sorted_meta[0]["to"]

        for meta in sorted_meta[1:]:
            next_from   = meta["from"]
            next_to     = meta["to"]

            # Перекрытие: next_from <= current_to (лексикографическое сравнение)
            if next_from <= current_to:
                # Расширить текущий диапазон, если next дальше
                if next_to > current_to:
                    current_to = next_to
            else:
                merged.append({"from": current_from, "to": current_to})
                current_from = next_from
                current_to = next_to

        merged.append({"from": current_from, "to": current_to})

        # Получить текст для каждого объединённого диапазона
        result: list[TChunk] = []
        for m in merged:
            result.append(self.getChunk(m["from"], m["to"]))

        return result
