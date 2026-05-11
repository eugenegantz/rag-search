import unittest
from unittest.mock import patch, MagicMock
from core.readers.WebChunkReader import WebChunkReader


class TestWebChunkReader(unittest.TestCase):
    def setUp(self):
        self.patch_get = patch("core.readers.WebChunkReader.requests.get")
        self.MockGet = self.patch_get.start()
        self.addCleanup(self.patch_get.stop)

    def _setup(self, html_text: str):
        mock_response = MagicMock()
        mock_response.text = html_text
        self.MockGet.return_value = mock_response
        return WebChunkReader("https://example.com")

    def test_is_loaded_and_load(self):
        reader = self._setup("<html><body><p>Hello world.</p></body></html>")
        self.assertFalse(reader.is_loaded())
        reader.load()
        self.assertTrue(reader.is_loaded())
        reader.load()
        self.assertTrue(reader.is_loaded())

    def test_createChunks(self):
        reader = self._setup("<html><body><p>Hello world.</p></body></html>")
        chunks = reader.createChunks()
        self.assertGreater(len(chunks), 0)
        full = " ".join(c["text"] for c in chunks)
        self.assertIn("Hello world.", full)

    def test_user_agent_header(self):
        reader = self._setup("<html></html>")
        reader.createChunks()
        self.MockGet.assert_called_once()
        _, kwargs = self.MockGet.call_args
        self.assertIn("User-Agent", kwargs["headers"])
        self.assertIn("Mozilla", kwargs["headers"]["User-Agent"])

    def test_coords_are_char_idx(self):
        reader = self._setup("<html><body>ABC</body></html>")
        chars = list(reader._chars_with_coords())
        self.assertEqual(chars[0], ("A", (0,)))

    def test_getChunk(self):
        reader = self._setup("<html><body>Hello world.</body></html>")
        chunk = reader.getChunk([0], [4])
        self.assertEqual(chunk["text"], "Hello")

    def test_coords_integrity(self):
        reader = self._setup("<html><body>First sentence. Second sentence.</body></html>")
        for chunk in reader.createChunks():
            extracted = reader.getChunk(chunk["from"], chunk["to"])
            self.assertIn(chunk["text"], extracted["text"])


if __name__ == "__main__":
    unittest.main()
