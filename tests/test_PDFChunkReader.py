import unittest
from unittest.mock import patch, MagicMock
from core.readers.PDFChunkReader import PDFChunkReader


class TestPDFChunkReader(unittest.TestCase):
    def setUp(self):
        self.patch_reader = patch("core.readers.PDFChunkReader.PdfReader")
        self.MockReader = self.patch_reader.start()
        self.addCleanup(self.patch_reader.stop)

    def _setup_pages(self, pages_text: list[str]):
        mock_reader = MagicMock()
        mock_pages = []
        for text in pages_text:
            page = MagicMock()
            page.extract_text.return_value = text
            mock_pages.append(page)
        mock_reader.pages = mock_pages
        self.MockReader.return_value = mock_reader
        return PDFChunkReader("dummy.pdf")

    def test_is_loaded_and_load(self):
        reader = self._setup_pages(["Hello world."])
        self.assertFalse(reader.is_loaded())
        reader.load()
        self.assertTrue(reader.is_loaded())
        reader.load()
        self.assertTrue(reader.is_loaded())

    def test_single_page(self):
        reader = self._setup_pages(["Hello world."])
        chunks = reader.createChunks()
        self.assertGreater(len(chunks), 0)
        full = " ".join(c["text"] for c in chunks)
        self.assertIn("Hello world.", full)

    def test_multi_page(self):
        reader = self._setup_pages(["Page one. ", "Page two."])
        chunks = reader.createChunks()
        full = " ".join(c["text"] for c in chunks)
        self.assertIn("Page one.", full)
        self.assertIn("Page two.", full)

    def test_coords_are_page_char(self):
        reader = self._setup_pages(["AB", "CD"])
        chars = list(reader._chars_with_coords())
        self.assertEqual(chars[0], ("A", (0, 0)))
        self.assertEqual(chars[1], ("B", (0, 1)))
        self.assertEqual(chars[2], ("C", (1, 0)))
        self.assertEqual(chars[3], ("D", (1, 1)))

    def test_getChunk_single_page(self):
        reader = self._setup_pages(["Hello world."])
        chunk = reader.getChunk([0, 0], [0, 4])
        self.assertEqual(chunk["text"], "Hello")

    def test_getChunk_across_pages(self):
        reader = self._setup_pages(["Page one.", "Page two."])
        chunk = reader.getChunk([0, 5], [1, 8])
        self.assertEqual(chunk["text"], "one. Page two.")

    def test_coords_integrity(self):
        reader = self._setup_pages(["First sentence. Second sentence."])
        for chunk in reader.createChunks():
            extracted = reader.getChunk(chunk["from"], chunk["to"])
            self.assertIn(chunk["text"], extracted["text"])


if __name__ == "__main__":
    unittest.main()
