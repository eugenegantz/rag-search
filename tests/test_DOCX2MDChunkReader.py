import unittest
from unittest.mock import patch, MagicMock, mock_open
from core.readers.DOCX2MDChunkReader import DOCX2MDChunkReader


class TestDOCX2MDChunkReader(unittest.TestCase):
    def setUp(self):
        self.patch_convert = patch("core.readers.DOCX2MDChunkReader.mammoth.convert_to_html")
        self.MockConvert = self.patch_convert.start()
        self.addCleanup(self.patch_convert.stop)

        self.patch_html2text = patch("core.readers.DOCX2MDChunkReader.html2text.HTML2Text")
        self.MockHTML2Text = self.patch_html2text.start()
        self.addCleanup(self.patch_html2text.stop)

        self.patch_open = patch("builtins.open", mock_open(read_data=b""))
        self.MockOpen = self.patch_open.start()
        self.addCleanup(self.patch_open.stop)

    def _setup(self, html_text: str, md_text: str):
        mock_result = MagicMock()
        mock_result.value = html_text
        self.MockConvert.return_value = mock_result

        mock_converter = MagicMock()
        mock_converter.handle.return_value = md_text
        self.MockHTML2Text.return_value = mock_converter

        return DOCX2MDChunkReader("dummy.docx")

    def test_is_loaded_and_load(self):
        reader = self._setup("<p>Hello world.</p>", "Hello world.")
        self.assertFalse(reader.is_loaded())
        reader.load()
        self.assertTrue(reader.is_loaded())
        reader.load()
        self.assertTrue(reader.is_loaded())

    def test_createChunks(self):
        reader = self._setup("<p>Hello world.</p>", "Hello world.")
        chunks = reader.createChunks()
        self.assertGreater(len(chunks), 0)
        full = " ".join(c["text"] for c in chunks)
        self.assertIn("Hello world.", full)

    def test_coords_are_char_idx(self):
        reader = self._setup("<p>ABC</p>", "ABC")
        chars = list(reader._chars_with_coords())
        self.assertEqual(chars[0], ("A", (0,)))
        self.assertEqual(chars[1], ("B", (1,)))
        self.assertEqual(chars[2], ("C", (2,)))

    def test_getChunk(self):
        reader = self._setup("<p>Hello world.</p>", "Hello world.")
        chunk = reader.getChunk([0], [4])
        self.assertEqual(chunk["text"], "Hello")

    def test_coords_integrity(self):
        reader = self._setup(
            "<p>First sentence. Second sentence.</p>",
            "First sentence. Second sentence."
        )
        for chunk in reader.createChunks():
            extracted = reader.getChunk(chunk["from"], chunk["to"])
            self.assertIn(chunk["text"], extracted["text"])


if __name__ == "__main__":
    unittest.main()
