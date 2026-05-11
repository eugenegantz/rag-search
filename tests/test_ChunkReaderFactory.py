import unittest
from core.readers.ChunkReaderFactory import ChunkReaderFactory
from core.readers.TXTChunkReader import TXTChunkReader
from core.readers.MDChunkReader import MDChunkReader
from core.readers.HTMLChunkReader import HTMLChunkReader
from core.readers.PDFChunkReader import PDFChunkReader
from core.readers.DOCX2MDChunkReader import DOCX2MDChunkReader
from core.readers.WebChunkReader import WebChunkReader


class TestChunkReaderFactory(unittest.TestCase):
    def test_txt(self):
        reader = ChunkReaderFactory.get_reader("file.txt")
        self.assertIsInstance(reader, TXTChunkReader)

    def test_md(self):
        reader = ChunkReaderFactory.get_reader("file.md")
        self.assertIsInstance(reader, MDChunkReader)

    def test_html(self):
        reader = ChunkReaderFactory.get_reader("file.html")
        self.assertIsInstance(reader, HTMLChunkReader)

    def test_docx(self):
        reader = ChunkReaderFactory.get_reader("file.docx")
        self.assertIsInstance(reader, DOCX2MDChunkReader)

    def test_pdf(self):
        reader = ChunkReaderFactory.get_reader("file.pdf")
        self.assertIsInstance(reader, PDFChunkReader)

    def test_http(self):
        reader = ChunkReaderFactory.get_reader("http://example.com")
        self.assertIsInstance(reader, WebChunkReader)

    def test_https(self):
        reader = ChunkReaderFactory.get_reader("https://example.com")
        self.assertIsInstance(reader, WebChunkReader)

    def test_case_insensitive_url(self):
        reader = ChunkReaderFactory.get_reader("HTTPS://EXAMPLE.COM")
        self.assertIsInstance(reader, WebChunkReader)

    def test_unsupported_raises(self):
        with self.assertRaises(ValueError) as ctx:
            ChunkReaderFactory.get_reader("file.xyz")
        self.assertIn("Unsupported file format", str(ctx.exception))

    def test_uppercase_extension(self):
        reader = ChunkReaderFactory.get_reader("FILE.TXT")
        self.assertIsInstance(reader, TXTChunkReader)


if __name__ == "__main__":
    unittest.main()
