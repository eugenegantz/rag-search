import typing
import requests
import html2text
from core.chunking import create_chunks_with_coords
from core.readers.BaseChunkReader import BaseChunkReader
from core.types import TChunk


class WebChunkReader(BaseChunkReader):
    """Ридер для веб-URL. Делает HTTP-запрос при первом чтении. Координаты: [char_start, char_end]."""

    def __init__(self, url: str):
        self.url = url
        self._text: str = ""
        self._loaded = False


    def load(self) -> None:
        if self._loaded:
            return

        converter = html2text.HTML2Text()
        converter.bypass_tables = False
        converter.ignore_links = False
        converter.ignore_images = False
        converter.ignore_emphasis = False

        res = requests.get(
            self.url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
            }
        )

        self._text = converter.handle(res.text)
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
            delimiters=[" ", "\n"],
        )


    def createChunks(self) -> list[TChunk]:
        return [chunk for chunk in self.createChunksIterator()]
