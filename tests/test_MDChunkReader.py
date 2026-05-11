import os
import tempfile
import unittest
from core.readers.MDChunkReader import MDChunkReader


class TestMDChunkReader(unittest.TestCase):
    def setUp(self):
        self.fp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".md")
        self.fp.write("# Title\n\nFirst paragraph. Second sentence.\n\nAnother paragraph.")
        self.fp.close()
        self.reader = MDChunkReader(self.fp.name)

    def tearDown(self):
        os.unlink(self.fp.name)

    def test_createChunks(self):
        chunks = self.reader.createChunks()
        self.assertGreater(len(chunks), 0)
        full = " ".join(c["text"] for c in chunks)
        self.assertIn("Title", full)
        self.assertIn("First paragraph.", full)

    def test_coords_integrity(self):
        for chunk in self.reader.createChunks():
            extracted = self.reader.getChunk(chunk["from"], chunk["to"])
            self.assertIn(chunk["text"], extracted["text"])


if __name__ == "__main__":
    unittest.main()
