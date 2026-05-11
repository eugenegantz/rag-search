import os
import tempfile
import unittest
from core.readers.BaseTextChunkReader import BaseTextChunkReader


class TestBaseTextChunkReader(unittest.TestCase):
    def setUp(self):
        self.fp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt")
        self.fp.write("Hello world. Second sentence.")
        self.fp.close()
        self.reader = BaseTextChunkReader(self.fp.name, delimiters=[" "])

    def tearDown(self):
        os.unlink(self.fp.name)

    def test_lazy_load(self):
        self.assertFalse(self.reader.is_loaded())
        self.reader.load()
        self.assertTrue(self.reader.is_loaded())
        self.reader.load()
        self.assertTrue(self.reader.is_loaded())

    def test_getChunk(self):
        chunk = self.reader.getChunk([0], [4])
        self.assertEqual(chunk["text"], "Hello")
        self.assertEqual(chunk["from"], [0])
        self.assertEqual(chunk["to"], [4])

    def test_getChunk_end_inclusive(self):
        chunk = self.reader.getChunk([6], [10])
        self.assertEqual(chunk["text"], "world")

    def test_createChunks(self):
        chunks = self.reader.createChunks()
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertIn("text", chunk)
            self.assertIn("from", chunk)
            self.assertIn("to", chunk)

    def test_createChunks_idempotent(self):
        chunks1 = self.reader.createChunks()
        chunks2 = self.reader.createChunks()
        self.assertEqual(len(chunks1), len(chunks2))
        for c1, c2 in zip(chunks1, chunks2):
            self.assertEqual(c1["text"], c2["text"])
            self.assertEqual(c1["from"], c2["from"])
            self.assertEqual(c1["to"], c2["to"])

    def test_coords_integrity(self):
        for chunk in self.reader.createChunks():
            extracted = self.reader.getChunk(chunk["from"], chunk["to"])
            self.assertIn(chunk["text"], extracted["text"])


if __name__ == "__main__":
    unittest.main()
