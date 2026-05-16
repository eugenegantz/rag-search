import typing
from core.types import TChunk

SEQ_LEN_LIM = 1024
LARGE_INT = 999_999_999_999

TWordIteratorResult = typing.Iterable[
    tuple[
        str,
        tuple[int, ...],
        tuple[int, ...],
    ]
]

TCharsIteratorResult = typing.Iterable[
    tuple[
        str,
        tuple[int, ...],
    ]
]

def create_words_with_coords(
    chars_with_coords: TCharsIteratorResult,
    delimiters: list[str] = [" ", "\n"],
) -> TWordIteratorResult:
    """Преобразует итератор символов в итератор слов с координатами."""
    word = ""
    start: tuple[int, ...] = tuple()
    end: tuple[int, ...] = tuple()

    for char, coord in chars_with_coords:
        if char in delimiters:
            if word:
                yield word, start, end
                word = ""
                start = tuple()
        else:
            if not start:
                start = coord
            word += char
            end = coord

    if word:
        yield word, start, end


def create_sentences_with_coords(
    words_with_coords: TWordIteratorResult,
    chunk_size: int = SEQ_LEN_LIM
):
    """Возвращает предложения из итератора слов.

    Каждое предложение — последовательность слов, разделённых пробелами,
    которая заканчивается точкой (.), вопросительным (?) или
    восклицательным (!) знаком.
    Длина предложения не превышает chunk_size (символы).
    Если накопленный текст превышает chunk_size, возвращает накопленное
    до текущего слова и начинает новый буфер.
    Слова длиннее chunk_size пропускаются (аномалия).
    """
    sentence_text = ""
    sentence_start: tuple[int, ...] = tuple()
    sentence_end: tuple[int, ...] = tuple()
    END_OF_SENTENCE_MARKS = ".?!"

    for word, word_start, word_end in words_with_coords:
        word = word.strip(" ")

        if not word:
            continue

        # Аномалия: слово длиннее chunk_size.
        # Возможно в будущем здесь стоит добавить исключение.
        if len(word) > chunk_size:
            continue

        separator = 1 if sentence_text else 0
        candidate_len = len(sentence_text) + separator + len(word)

        if candidate_len > chunk_size:
            if sentence_text:
                yield sentence_text, sentence_start, sentence_end
            sentence_text = word
            sentence_start = word_start
            sentence_end = word_end
        else:
            if sentence_text:
                sentence_text += " "
            else:
                sentence_start = word_start
            sentence_text += word
            sentence_end = word_end

        if sentence_text and sentence_text[-1] in END_OF_SENTENCE_MARKS:
            yield sentence_text, sentence_start, sentence_end
            sentence_text = ""
            sentence_start = tuple()
            sentence_end = tuple()

    if sentence_text:
        yield sentence_text, sentence_start, sentence_end


def create_chunks_with_coords(
    chars_with_coords: typing.Iterable[tuple[str, tuple[int, ...]]],
    chunk_size: int = SEQ_LEN_LIM,
    delimiters: list[str] = [" ", "\n"],
) -> typing.Iterator[TChunk]:
    """Потоковое создание чанков из итератора по символам (char, coord).

    Каждый chunk — последовательность предложений, разделённых пробелами.
    Длина chunk не превышает chunk_size (символы).
    Если накопленный текст превышает chunk_size, возвращает накопленное
    до текущего предложения и начинает новый chunk.
    coord — кортеж координат произвольной длины: (char_idx,) или (page, char_idx) и т.д.
    """
    chunk_text = ""
    chunk_start: tuple[int, ...] = tuple()
    chunk_end: tuple[int, ...] = tuple()

    for sentence, sentence_start, sentence_end in create_sentences_with_coords(
        create_words_with_coords(chars_with_coords, delimiters),
        chunk_size
    ):
        separator = 1 if chunk_text else 0
        candidate_len = len(chunk_text) + separator + len(sentence)

        if candidate_len > chunk_size:
            if chunk_text:
                yield {
                    "text": chunk_text,
                    "from": list(chunk_start),
                    "to": list(chunk_end),
                }
            chunk_text = sentence
            chunk_start = sentence_start
            chunk_end = sentence_end
        else:
            if chunk_text:
                chunk_text += " "
            else:
                chunk_start = sentence_start
            chunk_text += sentence
            chunk_end = sentence_end

    if chunk_text:
        yield {
            "text": chunk_text,
            "from": list(chunk_start),
            "to": list(chunk_end),
        }


def expand_1d(
    from_: list[int],
    to_: list[int],
    paddings: int,
    min_index: int = 0,
    max_index: int = LARGE_INT,
) -> tuple[list[int], list[int]]:
    """Расширить 1D координаты чанка."""
    from_ = from_.copy()
    to_ = to_.copy()

    from_[0] = max(min_index, from_[0] - paddings)
    to_[0] = min(max_index, to_[0] + paddings)

    return from_, to_


def expand_2d(
    from_: list[int],
    to_: list[int],
    paddings: int,
    min_index: int = 0,
    max_index: int = LARGE_INT,
) -> tuple[list[int], list[int]]:
    """Расширить 2D координаты чанка [page/para, char_idx]."""
    from_ = from_.copy()
    to_ = to_.copy()

    from_[1] = max(min_index, from_[1] - paddings)
    to_[1] = min(max_index, to_[1] + paddings)

    return from_, to_
