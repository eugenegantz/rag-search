import os
import tempfile
import unittest
from core.readers.HTMLChunkReader import HTMLChunkReader


class TestHTMLChunkReader(unittest.TestCase):
    def setUp(self):
        self.fp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".html")
        self.fp.write("<html><body><p>Hello world.</p><p>Second paragraph.</p></body></html>")
        self.fp.close()
        self.reader = HTMLChunkReader(self.fp.name)

    def tearDown(self):
        os.unlink(self.fp.name)

    def test_is_loaded_and_load(self):
        self.assertFalse(self.reader.is_loaded())
        self.reader.load()
        self.assertTrue(self.reader.is_loaded())
        self.reader.load()
        self.assertTrue(self.reader.is_loaded())

    def test_createChunks(self):
        chunks = self.reader.createChunks()
        self.assertGreater(len(chunks), 0)
        full = " ".join(c["text"] for c in chunks)
        self.assertIn("Hello world.", full)
        self.assertIn("Second paragraph.", full)

    def test_html_stripped(self):
        chunks = self.reader.createChunks()
        for chunk in chunks:
            self.assertNotIn("<html>", chunk["text"])
            self.assertNotIn("<p>", chunk["text"])

    def test_coords_are_char_idx(self):
        chunk = self.reader.getChunk([0], [4])
        self.assertEqual(chunk["text"], "Hello")

    def test_coords_integrity(self):
        for chunk in self.reader.createChunks():
            extracted = self.reader.getChunk(chunk["from"], chunk["to"])
            self.assertIn(chunk["text"], extracted["text"])


if __name__ == "__main__":
    unittest.main()
