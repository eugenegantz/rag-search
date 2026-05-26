import os
from pathlib import Path

import chromadb
from transformers import pipeline, AutoModel, AutoTokenizer

from app_config.config import config
from core.deps.default_logger import default_logger

DEFAULT_MODEL_NAME = "intfloat/multilingual-e5-large"
DEFAULT_DB_PATH = "./db"
DEFAULT_COLLECTION_NAME = "rag_search"

MODEL_LOCAL_PATH = Path("./models") / DEFAULT_MODEL_NAME

_device_map = config["embeddings"]["device_map"]

# Если локальная модель не найдена -- скачать из репозитория
if MODEL_LOCAL_PATH.exists() and any(MODEL_LOCAL_PATH.iterdir()):
    default_logger.info(f"Loading local model from {MODEL_LOCAL_PATH}")

    model = AutoModel.from_pretrained(
        str(MODEL_LOCAL_PATH),
        local_files_only=True,
        device_map=_device_map,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        str(MODEL_LOCAL_PATH),
        local_files_only=True,
        device_map=_device_map,
    )

else:
    default_logger.info(f"Local model not found in {MODEL_LOCAL_PATH}. Downloading from HuggingFace...")

    os.makedirs(MODEL_LOCAL_PATH, exist_ok=True)

    # Скачать модель из репозитория
    model = AutoModel.from_pretrained(
        DEFAULT_MODEL_NAME,
        device_map=_device_map,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        DEFAULT_MODEL_NAME,
        device_map=_device_map,
    )

    # Сохранить модель локально
    model.save_pretrained(MODEL_LOCAL_PATH)     # type: ignore
    tokenizer.save_pretrained(MODEL_LOCAL_PATH) # type: ignore

    default_logger.info(f"Model saved to {MODEL_LOCAL_PATH}")

print("[DEBUG] model.device =", model.device)

pipe = pipeline(
    "feature-extraction",
    model=model,
    tokenizer=tokenizer,
    device=model.device,
)  # type: ignore
db = chromadb.PersistentClient(path=DEFAULT_DB_PATH)