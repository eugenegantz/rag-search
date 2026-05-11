from core.readers.BaseTextChunkReader import BaseTextChunkReader


class TXTChunkReader(BaseTextChunkReader):
    def __init__(self, filepath: str):
        super().__init__(filepath, delimiters=[" ", "\n", "\t"])
