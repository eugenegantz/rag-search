import unittest
from unittest.mock import patch, MagicMock
from core.readers.DOCXChunkReader import DOCXChunkReader


class TestDOCXChunkReader(unittest.TestCase):
    def setUp(self):
        self.patch_doc = patch("core.readers.DOCXChunkReader.docx.Document")
        self.MockDoc = self.patch_doc.start()
        self.addCleanup(self.patch_doc.stop)

    def _setup_paras(self, paragraphs: list[str]):
        mock_doc = MagicMock()
        mock_paras = []
        for text in paragraphs:
            para = MagicMock()
            para.text = text
            mock_paras.append(para)
        mock_doc.paragraphs = mock_paras
        self.MockDoc.return_value = mock_doc
        return DOCXChunkReader("dummy.docx")

    def test_is_loaded_and_load(self):
        reader = self._setup_paras(["Hello world."])
        self.assertFalse(reader.is_loaded())
        reader.load()
        self.assertTrue(reader.is_loaded())
        reader.load()
        self.assertTrue(reader.is_loaded())

    def test_single_paragraph(self):
        reader = self._setup_paras(["Hello world."])
        chunks = reader.createChunks()
        self.assertGreater(len(chunks), 0)
        full = " ".join(c["text"] for c in chunks)
        self.assertIn("Hello world.", full)

    def test_multi_paragraph(self):
        reader = self._setup_paras(["First para.", "Second para."])
        chunks = reader.createChunks()
        full = " ".join(c["text"] for c in chunks)
        self.assertIn("First para.", full)
        self.assertIn("Second para.", full)

    def test_coords_are_para_char(self):
        reader = self._setup_paras(["AB", "CD"])
        chars = list(reader._chars_with_coords())
        self.assertEqual(chars[0], ("A", (0, 0)))
        self.assertEqual(chars[1], ("B", (0, 1)))
        self.assertEqual(chars[2], ("\n", (0, 2)))
        self.assertEqual(chars[3], ("\n", (0, 3)))
        self.assertEqual(chars[4], ("C", (1, 0)))

    def test_getChunk_single_para(self):
        reader = self._setup_paras(["Hello world."])
        chunk = reader.getChunk([0, 0], [0, 4])
        self.assertEqual(chunk["text"], "Hello")

    def test_getChunk_across_paras(self):
        reader = self._setup_paras(["First para.", "Second para."])
        chunk = reader.getChunk([0, 6], [1, 11])
        self.assertEqual(chunk["text"], "para. Second para.")

    def test_coords_integrity(self):
        reader = self._setup_paras(["First sentence. Second sentence."])
        for chunk in reader.createChunks():
            extracted = reader.getChunk(chunk["from"], chunk["to"])
            # getChunk объединяет параграфы через пробел, тогда как чанки содержат \n\n
            # от _chars_with_coords — проверяем что текст без \n входит в extracted
            clean_chunk = chunk["text"].replace("\n", " ").strip()
            self.assertIn(clean_chunk, extracted["text"])


if __name__ == "__main__":
    unittest.main()
