import unittest
from core.readers.BaseChunkReader import BaseChunkReader
from core.types import TChunk, TChunkArgs


class MockChunkReader(BaseChunkReader):
    """Тестовая реализация BaseChunkReader для проверки getChunks."""

    def __init__(self, text: str = ""):
        self.text = text

    def getChunk(self, from_: list[int], to: list[int]) -> TChunk:
        start = from_[0]
        end = to[0] + 1
        return {
            "text": self.text[start:end],
            "from": from_,
            "to": to,
        }

    def createChunks(self) -> list[TChunk]:
        return []

    def createChunksIterator(self):
        return iter([])

    def load(self) -> None:
        pass

    def is_loaded(self) -> bool:
        return True


class TestBaseChunkReaderGetChunks(unittest.TestCase):
    def setUp(self):
        self.reader = MockChunkReader("ABCDEFGHIJ")

    def test_empty_list(self):
        result = self.reader.getChunks([])
        self.assertEqual(result, [])

    def test_single_chunk(self):
        meta: list[TChunkArgs] = [{"from": [0], "to": [4]}]
        result = self.reader.getChunks(meta)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "ABCDE")

    def test_sorting(self):
        meta: list[TChunkArgs] = [
            {"from": [5], "to": [7]},
            {"from": [0], "to": [2]},
        ]
        result = self.reader.getChunks(meta)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["text"], "ABC")
        self.assertEqual(result[1]["text"], "FGH")

    def test_overlapping_ranges_merged(self):
        meta: list[TChunkArgs] = [
            {"from": [0], "to": [3]},
            {"from": [2], "to": [5]},
        ]
        result = self.reader.getChunks(meta)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "ABCDEF")

    def test_adjacent_ranges_merged(self):
        """Смежные диапазоны (next_from == current_to) объединяются."""
        meta: list[TChunkArgs] = [
            {"from": [0], "to": [3]},
            {"from": [3], "to": [6]},
        ]
        result = self.reader.getChunks(meta)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "ABCDEFG")

    def test_non_overlapping_ranges(self):
        meta: list[TChunkArgs] = [
            {"from": [0], "to": [2]},
            {"from": [5], "to": [7]},
        ]
        result = self.reader.getChunks(meta)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["text"], "ABC")
        self.assertEqual(result[1]["text"], "FGH")

    def test_nested_ranges(self):
        meta: list[TChunkArgs] = [
            {"from": [0], "to": [6]},
            {"from": [2], "to": [4]},
        ]
        result = self.reader.getChunks(meta)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "ABCDEFG")

    def test_multi_coords_lexicographic(self):
        reader = MockChunkReader("0123456789")
        meta: list[TChunkArgs] = [
            {"from": [1, 0], "to": [1, 3]},
            {"from": [0, 5], "to": [0, 8]},
        ]
        result = reader.getChunks(meta)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["from"], [0, 5])
        self.assertEqual(result[1]["from"], [1, 0])


if __name__ == "__main__":
    unittest.main()
