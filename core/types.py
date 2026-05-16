import typing

class TConfigDaemon(typing.TypedDict):
    host: str
    port: int

class TConfigOpenAI(typing.TypedDict):
    base_url: str
    api_key: str
    default_headers: typing.NotRequired[dict[str, str]]
    model: str

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
    "rtype": str,
    "from": list[int],
    "to": list[int],
})

class TContextEntry(typing.TypedDict):
    filepath: str
    content: str
    rtype: str


class TRagSearchResRef(typing.TypedDict):
    filepath: str
    note: str


class TRagSearchResult(typing.TypedDict):
    # error: str
    content: str
    refs: list[dict[str, typing.Any]]


if typing.TYPE_CHECKING:
    # from transformers.generation.utils import GenerationMixin
    from torch import Tensor

    # 1. Define a singular interface handling both generation and attributes
    class GeneratableModel(typing.Protocol):
        def generate(self, **kwargs: typing.Any) -> Tensor: ...

        # This mirrors all standard properties from the true model class
        def __getattr__(self, name: str) -> typing.Any: ...
