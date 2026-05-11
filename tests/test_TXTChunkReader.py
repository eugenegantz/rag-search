import os
import tempfile
import unittest
from core.readers.TXTChunkReader import TXTChunkReader


class TestTXTChunkReader(unittest.TestCase):
    def setUp(self):
        self.fp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt")
        self.fp.write("Hello world.\nSecond line.\tThird word.")
        self.fp.close()
        self.reader = TXTChunkReader(self.fp.name)

    def tearDown(self):
        os.unlink(self.fp.name)

    def test_createChunks(self):
        chunks = self.reader.createChunks()
        self.assertGreater(len(chunks), 0)
        full = " ".join(c["text"] for c in chunks)
        self.assertIn("Hello world.", full)
        self.assertIn("Second line.", full)
        self.assertIn("Third word.", full)

    def test_getChunk_by_coords(self):
        chunk = self.reader.getChunk([0], [4])
        self.assertEqual(chunk["text"], "Hello")

    def test_delimiters_include_tabs_and_newlines(self):
        chunks = self.reader.createChunks()
        for chunk in chunks:
            self.assertNotIn("\t", chunk["text"])
            self.assertNotIn("\n", chunk["text"])

    def test_empty_file(self):
        fp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt")
        fp.write("")
        fp.close()
        reader = TXTChunkReader(fp.name)
        chunks = reader.createChunks()
        self.assertEqual(chunks, [])
        os.unlink(fp.name)


if __name__ == "__main__":
    unittest.main()
