import typing

class TConfigDaemon(typing.TypedDict):
    host: str
    port: int

class TConfigOpenAI(typing.TypedDict):
    base_url: str
    api_key: str
    default_headers: typing.NotRequired[dict[str, str]]

class TConfig(typing.TypedDict):
    openai: TConfigOpenAI
    daemon: TConfigDaemon

TChunk = typing.TypedDict("TChunk", {
    "text": str,
    "from": list[int],
    "to": list[int],
})

TChunkArgs = typing.TypedDict("TChunkArgs", {
    "from": list[int],
    "to": list[int],
})

TCDBMetaEntry = typing.TypedDict('TCDBMetaEntry', {
    "filepath": str,
    "from": list[int],
    "to": list[int],
})

class TContextEntry(typing.TypedDict):
    filepath: str
    content: str


class TRagSearchResRef(typing.TypedDict):
    filepath: str
    note: str


class TRagSearchResult(typing.TypedDict):
    # error: str
    content: str
    refs: list[dict[str, typing.Any]]
