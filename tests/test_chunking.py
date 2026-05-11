import unittest
from core.chunking import (
    create_words_with_coords,
    create_sentences_with_coords,
    create_chunks_with_coords,
    SEQ_LEN_LIM,
)


class TestCreateWordsWithCoords(unittest.TestCase):
    def test_empty(self):
        result = list(create_words_with_coords(iter([])))
        self.assertEqual(result, [])

    def test_simple(self):
        chars = [(c, (i,)) for i, c in enumerate("Hello world")]
        result = list(create_words_with_coords(chars))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ("Hello", (0,), (4,)))
        self.assertEqual(result[1], ("world", (6,), (10,)))

    def test_multiple_spaces(self):
        chars = [(c, (i,)) for i, c in enumerate("a  b")]
        result = list(create_words_with_coords(chars))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ("a", (0,), (0,)))
        self.assertEqual(result[1], ("b", (3,), (3,)))

    def test_newline_delimiter(self):
        chars = [(c, (i,)) for i, c in enumerate("line1\nline2")]
        result = list(create_words_with_coords(chars))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ("line1", (0,), (4,)))
        self.assertEqual(result[1], ("line2", (6,), (10,)))

    def test_custom_delimiters(self):
        chars = [(c, (i,)) for i, c in enumerate("a,b.c")]
        result = list(create_words_with_coords(chars, delimiters=[",", "."]))
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], ("a", (0,), (0,)))
        self.assertEqual(result[1], ("b", (2,), (2,)))
        self.assertEqual(result[2], ("c", (4,), (4,)))

    def test_trailing_delimiter(self):
        chars = [(c, (i,)) for i, c in enumerate("word ")]
        result = list(create_words_with_coords(chars))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ("word", (0,), (3,)))

    def test_only_delimiters(self):
        chars = [(c, (i,)) for i, c in enumerate("   \n\n")]
        result = list(create_words_with_coords(chars))
        self.assertEqual(result, [])


class TestCreateSentencesWithCoords(unittest.TestCase):
    def test_empty(self):
        result = list(create_sentences_with_coords(iter([])))
        self.assertEqual(result, [])

    def test_simple_sentence(self):
        words = [
            ("Hello", (0,), (4,)),
            ("world!", (6,), (11,)),
        ]
        result = list(create_sentences_with_coords(words))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "Hello world!")
        self.assertEqual(result[0][1], (0,))
        self.assertEqual(result[0][2], (11,))

    def test_multiple_sentences(self):
        words = [
            ("First", (0,), (4,)),
            ("sentence.", (6,), (14,)),
            ("Second", (16,), (21,)),
            ("one?", (23,), (26,)),
        ]
        result = list(create_sentences_with_coords(words))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], "First sentence.")
        self.assertEqual(result[1][0], "Second one?")

    def test_chunk_size_split(self):
        chunk_size = 10
        words = [
            ("12345", (0,), (4,)),
            ("67890", (6,), (10,)),
            ("abcde", (12,), (16,)),
        ]
        result = list(create_sentences_with_coords(words, chunk_size=chunk_size))
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][0], "12345")
        self.assertEqual(result[1][0], "67890")
        self.assertEqual(result[2][0], "abcde")

    def test_word_longer_than_chunk_size_skipped(self):
        chunk_size = 5
        words = [
            ("short", (0,), (4,)),
            ("verylongword", (6,), (17,)),
            ("end.", (19,), (22,)),
        ]
        result = list(create_sentences_with_coords(words, chunk_size=chunk_size))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], "short")
        self.assertEqual(result[1][0], "end.")

    def test_no_end_mark(self):
        words = [
            ("No", (0,), (1,)),
            ("ending", (3,), (8,)),
        ]
        result = list(create_sentences_with_coords(words))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "No ending")

    def test_coords_propagation(self):
        words = [
            ("A", (0, 0), (0, 0)),
            ("B.", (0, 2), (0, 3)),
        ]
        result = list(create_sentences_with_coords(words))
        self.assertEqual(result[0][1], (0, 0))
        self.assertEqual(result[0][2], (0, 3))


class TestCreateChunksWithCoords(unittest.TestCase):
    def test_empty(self):
        result = list(create_chunks_with_coords(iter([])))
        self.assertEqual(result, [])

    def test_single_chunk(self):
        chars = [(c, (i,)) for i, c in enumerate("Hello world.")]
        result = list(create_chunks_with_coords(chars, chunk_size=100))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "Hello world.")
        self.assertEqual(result[0]["from"], [0])
        self.assertEqual(result[0]["to"], [11])

    def test_multiple_chunks(self):
        text = "First sentence. Second sentence. Third sentence."
        chars = [(c, (i,)) for i, c in enumerate(text)]
        result = list(create_chunks_with_coords(chars, chunk_size=20))
        self.assertGreater(len(result), 1)
        for chunk in result:
            self.assertLessEqual(len(chunk["text"]), 20)

    def test_coords_consistency(self):
        text = "One. Two. Three."
        chars = [(c, (i,)) for i, c in enumerate(text)]
        result = list(create_chunks_with_coords(chars, chunk_size=100))
        for chunk in result:
            start = chunk["from"][0]
            end = chunk["to"][0] + 1
            self.assertEqual(chunk["text"], text[start:end])

    def test_large_string_no_loss(self):
        text = "ABCDE " * 5000 + "End."
        chars = [(c, (i,)) for i, c in enumerate(text)]
        result = list(create_chunks_with_coords(chars, chunk_size=SEQ_LEN_LIM))
        reconstructed = " ".join(chunk["text"] for chunk in result)
        self.assertEqual(reconstructed, text)

    def test_large_string_coords_monotonic(self):
        text = "Word. " * 3000
        chars = [(c, (i,)) for i, c in enumerate(text)]
        result = list(create_chunks_with_coords(chars, chunk_size=SEQ_LEN_LIM))
        prev_end = -1
        for chunk in result:
            start = chunk["from"][0]
            end = chunk["to"][0]
            self.assertGreater(start, prev_end)
            prev_end = end


if __name__ == "__main__":
    unittest.main()
