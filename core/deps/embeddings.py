import os
import torch.nn.functional as F
import chromadb
import typing

from torch import Tensor
from pathlib import Path
from transformers import AutoModel, AutoTokenizer

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


def average_pool(
    last_hidden_states: Tensor,
    attention_mask: Tensor
) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

def pipe(
    input_texts: str,
    prefix: typing.Literal["query", "passage"],
):
    input_texts = prefix + ": " + input_texts

    batch_dict = tokenizer(
        input_texts,
        max_length=512,
        padding=True,
        truncation=True,
        return_tensors="pt"
    )

    outputs = model(**batch_dict)

    embeddings = average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])

    # L2 нормализация (p=2)
    embeddings = F.normalize(embeddings, p=2, dim=1)

    return [embeddings.tolist()]


db = chromadb.PersistentClient(path=DEFAULT_DB_PATH)