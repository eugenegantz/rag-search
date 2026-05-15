import re
from core.readers.BaseChunkReader import BaseChunkReader
from core.readers.TXTChunkReader import TXTChunkReader
from core.readers.MDChunkReader import MDChunkReader
from core.readers.HTMLChunkReader import HTMLChunkReader
from core.readers.PDFChunkReader import PDFChunkReader
# from core.readers.DOCXChunkReader import DOCXChunkReader
from core.readers.DOCX2MDChunkReader import DOCX2MDChunkReader
from core.readers.WebChunkReader import WebChunkReader
from core.readers.Image2TextReader import Image2TextReader


class ChunkReaderFactory:
    """Фабрика ридеров чанков. Возвращает корректный ридер по расширению файла или URL."""

    @staticmethod
    def get_reader(filepath_or_url: str) -> BaseChunkReader:
        if re.findall(r'^https?:', filepath_or_url, re.I):
            return WebChunkReader(filepath_or_url)

        lowered = filepath_or_url.lower().strip()

        if lowered.endswith('.html'):
            return HTMLChunkReader(filepath_or_url)

        elif lowered.endswith('.txt'):
            return TXTChunkReader(filepath_or_url)

        elif lowered.endswith('.md'):
            return MDChunkReader(filepath_or_url)

        elif lowered.endswith('.docx'):
            return DOCX2MDChunkReader(filepath_or_url)

        elif lowered.endswith('.pdf'):
            return PDFChunkReader(filepath_or_url)
        
        elif lowered.endswith(('.jpg', '.jpeg', '.png')):
            return Image2TextReader(filepath_or_url)

        raise ValueError(f"Unsupported file format: {filepath_or_url}")
