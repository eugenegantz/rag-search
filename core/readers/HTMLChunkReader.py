import typing
import html2text
from core.chunking import create_chunks_with_coords
from core.readers.BaseChunkReader import BaseChunkReader
from core.types import TChunk


class HTMLChunkReader(BaseChunkReader):
    """Ридер для HTML-файлов. Конвертирует HTML в текст через html2text. Координаты: [char_start, char_end]."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._text: str = ""
        self._loaded = False


    def load(self) -> None:
        if self._loaded:
            return

        with open(self.filepath, encoding="utf-8", mode="r") as fd:
            text_html = fd.read()

        converter = html2text.HTML2Text()
        converter.bypass_tables = False
        converter.ignore_links = False
        converter.ignore_images = False
        converter.ignore_emphasis = False

        self._text = converter.handle(text_html).strip()
        self._loaded = True


    def is_loaded(self) -> bool:
        return self._loaded


    def _chars_with_coords(self):
        self.load()

        for char_idx, char in enumerate(self._text):
            yield char, (char_idx,)


    def getChunk(self, from_: list[int], to: list[int]) -> TChunk:
        self.load()

        start   = from_[0]
        end     = to[0] + 1
        text    = self._text[start:end]

        return {
            "text": text,
            "from": from_,
            "to": to,
        }


    def createChunksIterator(self) -> typing.Iterator[TChunk]:
        return create_chunks_with_coords(
            self._chars_with_coords(),
            delimiters=[" "],
        )


    def createChunks(self) -> list[TChunk]:
        return [chunk for chunk in self.createChunksIterator()]
