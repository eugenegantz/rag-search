import typing

class TConfigDaemon(typing.TypedDict):
    host: str
    port: int

class TConfigOpenAI(typing.TypedDict):
    base_url: str
    api_key: str
    default_headers: dict[str, str]

class TConfig(typing.TypedDict):
    openai: TConfigOpenAI
    daemon: TConfigDaemon

class TCDBMetaEntry(typing.TypedDict):
    filepath: str
    chunk_index: int


class TContextEntry(typing.TypedDict):
    filepath: str
    chunk_index: int
    content: str


class TRagSearchResRef(typing.TypedDict):
    filepath: str
    note: str


class TRagSearchResult(typing.TypedDict):
    # error: str
    content: str
    refs: list[dict[str, typing.Any]]
