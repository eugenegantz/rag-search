import re
import typing
import docx
import html2text
import requests
from pypdf import PdfReader

SEQ_LEN_LIM = 1024


def words_iter(text: str, keep_lf: bool = False) -> typing.Generator[str]:
    word = ""
    for s in text:
        if s == " " or (s == "\n" and keep_lf == False):
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
        word = word.strip(" ")

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


def read_chunks_from_md_file(filepath: str, chunk_size: int = SEQ_LEN_LIM) -> list[str]: 
    with open(filepath, encoding="utf-8", mode="r") as fd:
        return create_chunks(words_iter(fd.read(), keep_lf=True), chunk_size)


def read_chunks_from_pdf_file(filepath: str, chunk_size: int = SEQ_LEN_LIM) -> list[str]:
    reader = PdfReader(filepath)

    def _iter():
        for page in reader.pages:
            text = page.extract_text()
            words = words_iter(text.strip())
            for word in words:
                yield word

    return create_chunks(_iter(), chunk_size)


def read_chunks_from_web_url(url: str, chunk_size: int = SEQ_LEN_LIM) -> list[str]:
    converter = html2text.HTML2Text()

    converter.bypass_tables     = False     # Конвертировать таблицы
    converter.ignore_links      = False     # Конвертировать ссылки
    converter.ignore_images     = False     # Конвертировать изображения
    converter.ignore_emphasis   = False     # Конвертировать жирный текст

    res = requests.get(
        url,
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
        }
    )

    text = converter.handle(res.text)

    return create_chunks(words_iter(text.strip(), keep_lf=True), chunk_size)


def read_chunks_from_html_file(filepath: str, chunk_size: int = SEQ_LEN_LIM) -> list[str]:
    with open(filepath, encoding="utf-8", mode="r") as fd:
        text_html = fd.read()

    converter = html2text.HTML2Text()

    converter.bypass_tables     = False     # Конвертировать таблицы
    converter.ignore_links      = False     # Конвертировать ссылки
    converter.ignore_images     = False     # Конвертировать изображения
    converter.ignore_emphasis   = False     # Конвертировать жирный текст

    text_md = converter.handle(text_html)

    return create_chunks(words_iter(text_md.strip(), keep_lf=True), chunk_size)


def read_chunks_from_file(url: str) -> list[str]:
    if re.findall(r'^https:|^http:', url, re.I):
        return read_chunks_from_web_url(url)

    elif re.findall(r'\.html$', url, re.I):
        return read_chunks_from_html_file(url)

    elif re.findall(r'\.txt$', url, re.I):
        return read_chunks_from_txt_file(url)

    elif re.findall(r'\.md$', url, re.I):
        return read_chunks_from_md_file(url)

    elif re.findall(r'\.docx$', url, re.I):
        return read_chunks_from_msdoc_file(url)

    elif re.findall(r'\.pdf$', url, re.I):
        return read_chunks_from_pdf_file(url)

    return []
