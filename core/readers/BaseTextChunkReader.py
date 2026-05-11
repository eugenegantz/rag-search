import typing
from core.chunking import create_chunks_with_coords
from core.readers.BaseChunkReader import BaseChunkReader
from core.types import TChunk


class BaseTextChunkReader(BaseChunkReader):
    """Базовый ридер для текстовых форматов с координатами [char_start, char_end]."""

    def __init__(self, filepath: str, delimiters: list[str] = [" "]):
        self.filepath = filepath
        self.delimiters = delimiters
        self._text: str = ""
        self._loaded = False


    def load(self) -> None:
        if self._loaded:
            return

        with open(self.filepath, encoding="utf-8", mode="r") as fd:
            self._text = fd.read()

        self._loaded = True


    def is_loaded(self) -> bool:
        return self._loaded


    def _chars_with_coords(self) -> typing.Iterator[tuple[str, tuple[int]]]:
        self.load()

        for char_idx, char in enumerate(self._text):
            yield char, (char_idx,)


    def getChunk(self, from_: list[int], to: list[int]) -> TChunk:
        self.load()

        start   = from_[0]
        end     = to[0] + 1  # включительно
        text    = self._text[start:end]

        return {
            "text": text,
            "from": from_,
            "to": to,
        }


    def createChunksIterator(self) -> typing.Iterator[TChunk]:
        return create_chunks_with_coords(
            self._chars_with_coords(),
            delimiters=self.delimiters
        )


    def createChunks(self) -> list[TChunk]:
        return [chunk for chunk in self.createChunksIterator()]