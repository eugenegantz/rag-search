import mammoth # type: ignore
import html2text
import typing
from core.chunking import create_chunks_with_coords
from core.readers.BaseChunkReader import BaseChunkReader
from core.types import TChunk


class DOCX2MDChunkReader(BaseChunkReader):
    """Ридер для DOCX-файлов. Координаты чанка: [char_idx]."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._text: str | None = None


    def load(self) -> None:
        if self._text is not None:
            return

        with open(self.filepath, "rb") as fd:
            # По неизвестной причине mammoth не умеет конвертировать docx таблицы в Markdown
            # Но, при этом, успешно конвертирует docx в HTML.

            # Конвертация в HTML
            text: str = mammoth.convert_to_html(fd).value # type: ignore
            text = typing.cast(str, text)

            converter = html2text.HTML2Text()
            converter.bypass_tables = False
            converter.ignore_links = False
            converter.ignore_images = False
            converter.ignore_emphasis = False

            # Конвертировать в Markdown
            text = converter.handle(text).strip()

            self._text = text


    def is_loaded(self) -> bool:
        return self._text is not None


    def _chars_with_coords(self):
        """Генератор символов с координатами [paragraph, char_idx] без накопления в памяти."""
        self.load()

        if self._text is None:
            raise Exception("self._text is None")

        for char_idx, char in enumerate(self._text):
            yield char, (char_idx, )


    def getChunk(self, from_: list[int], to: list[int]) -> TChunk:
        self.load()

        if self._text is None:
            raise Exception("self._text is None")

        start_char  = from_[0]
        end_char    = to[0]

        text = self._text[start_char:end_char + 1]

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
