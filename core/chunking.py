import re
import typing
import docx
from pypdf import PdfReader

SEQ_LEN_LIM = 1024


def words_iter(text: str) -> typing.Generator[str]:
    word = ""
    for s in text:
        if s == " " or s == "\n":
            if word:
                yield word
                word = ""
        else:
            word += s
    if word:
        yield word


def create_chunks(
    words: typing.Iterator[str],
    chunk_size: int = SEQ_LEN_LIM
) -> list[str]:
    chunks: list[str] = []
    chunk = ""
    sentence = ""

    for word in words:
        word = word.strip()
        if not word:
            continue

        if len(sentence) + len(word) + 1 > chunk_size:
            chunks.append(sentence.strip())
            chunk = ""
            sentence = ""
        sentence += (" " + word)

        if sentence[-1] == ".":
            if len(chunk) + len(sentence) > chunk_size:
                chunks.append(chunk.strip())
                chunk = ""
            chunk += sentence
            sentence = ""
    
    chunk += sentence
    chunks.append(chunk.strip())

    return chunks


def read_chunks_from_msdoc_file(filepath: str, chunk_size: int = SEQ_LEN_LIM) -> list[str]:
    doc = docx.Document(filepath)
    
    def _iter():
        for para in doc.paragraphs:
            words = words_iter(para.text.strip())
            for word in words:
                yield word
    
    return create_chunks(_iter(), chunk_size)


def read_chunks_from_txt_file(filepath: str, chunk_size: int = SEQ_LEN_LIM) -> list[str]: 
    with open(filepath, encoding="utf-8") as fd:
        return create_chunks(words_iter(fd.read()), chunk_size)


def read_chunks_from_pdf_file(filepath: str, chunk_size: int = SEQ_LEN_LIM) -> list[str]:
    reader = PdfReader(filepath)

    def _iter():
        for page in reader.pages:
            text = page.extract_text()
            words = words_iter(text.strip())
            for word in words:
                yield word

    return create_chunks(_iter(), chunk_size)


def read_chunks_from_file(filepath: str) -> list[str]:
    if re.findall(r'\.txt$', filepath, re.I):
        return read_chunks_from_txt_file(filepath)
    
    elif re.findall(r'\.docx$', filepath, re.I):
        return read_chunks_from_msdoc_file(filepath)
    
    elif re.findall(r'\.pdf$', filepath, re.I):
        return read_chunks_from_pdf_file(filepath)
    
    return []
