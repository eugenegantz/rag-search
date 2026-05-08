from core.RagSearch import RagSearch
from app_config.config import config

from core.deps.default_logger import default_logger
from core.deps.resource_indexer import resource_indexer

rag = RagSearch(
    resource_indexer=resource_indexer,
    logger=default_logger,
    openai_config=config['openai'],
)