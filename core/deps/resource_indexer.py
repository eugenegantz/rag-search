from core.ResourceIndexer import ResourceIndexer
from core.deps.default_logger import default_logger
from core.deps.embeddings import db, pipe, DEFAULT_COLLECTION_NAME

resource_indexer = ResourceIndexer(
    logger=default_logger,
    db=db,
    pipe=pipe,
    name=DEFAULT_COLLECTION_NAME,
)