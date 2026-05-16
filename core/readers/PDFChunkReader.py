import typing
from pypdf import PdfReader
from core.chunking import create_chunks_with_coords
from core.readers.BaseChunkReader import BaseChunkReader
from core.chunking import expand_2d
from core.types import TChunk
from core.utils.math import clamp

class PDFChunkReader(BaseChunkReader):
    """Ридер для PDF-файлов. Координаты чанка: [page, char_idx]."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._reader: PdfReader | None = None


    def load(self) -> None:
        if self._reader is None:
            self._reader = PdfReader(self.filepath)


    def is_loaded(self) -> bool:
        return self._reader is not None


    def _chars_with_coords(self) -> typing.Iterator[tuple[str, tuple[int, int]]]:
        """Генератор символов с координатами [page, char_idx] без накопления в памяти."""
        self.load()

        if self._reader is None:
            return

        for page_idx, page in enumerate(self._reader.pages):
            text = page.extract_text()
            for char_idx, char in enumerate(text):
                yield char, (page_idx, char_idx)


    def _expand_coords(self, from_: list[int], to_: list[int], paddings: int) -> tuple[list[int], list[int]]:
        return expand_2d(from_, to_, paddings)


    def getChunk(self, from_: list[int], to: list[int]) -> TChunk:
        self.load()

        if self._reader is None:
            raise Exception("reader is None")

        start_page, start_char  = from_
        end_page, end_char      = to
        texts: list[str]        = []

        if len(self._reader.pages) < 1:
            return {
                "text": "",
                "from": [0, 0],
                "to": [0, 0],
            }

        start_page = clamp(start_page, 0, len(self._reader.pages) - 1)
        end_page = clamp(end_page, 0, len(self._reader.pages) - 1)

        for page_idx in range(start_page, end_page + 1):
            page = self._reader.pages[page_idx]
            text = page.extract_text()

            if page_idx == start_page and page_idx == end_page:
                texts.append(text[start_char:end_char + 1])

            elif page_idx == start_page:
                texts.append(text[start_char:])

            elif page_idx == end_page:
                texts.append(text[:end_char + 1])

            else:
                texts.append(text)

        return {
            "text": " ".join(texts),
            "from": from_,
            "to": to,
        }


    def createChunksIterator(self) -> typing.Iterator[TChunk]:
        return create_chunks_with_coords(
            self._chars_with_coords(),
            delimiters=[" ", "\n"],
        )


    def createChunks(self) -> list[TChunk]:
        return [chunk for chunk in self.createChunksIterator()]
