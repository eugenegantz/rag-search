import os
import torch
import typing

from pathlib import Path
from transformers import AutoProcessor, AutoModelForImageTextToText
from core.deps.default_logger import default_logger

if typing.TYPE_CHECKING:
    from transformers import Qwen3VLProcessor
    from core.types import GeneratableModel

torch.set_num_threads(4)

# DEFAULT_MODEL_NAME = "Qwen/Qwen3.5-0.8B"
DEFAULT_MODEL_NAME = "huihui-ai/Huihui-Qwen3.5-0.8B-abliterated"

# Если локальная модель не найдена -- скачать из репозитория
MODEL_LOCAL_PATH = Path("./models") / DEFAULT_MODEL_NAME

_device_map = "auto"
_dtype = torch.float32

if MODEL_LOCAL_PATH.exists() and any(MODEL_LOCAL_PATH.iterdir()):
    default_logger.info(f"Loading local model from {MODEL_LOCAL_PATH}")

    processor: "Qwen3VLProcessor" = AutoProcessor.from_pretrained(str(MODEL_LOCAL_PATH), local_files_only=True) # type: ignore
    model: "GeneratableModel" = AutoModelForImageTextToText.from_pretrained(            # type: ignore
        str(MODEL_LOCAL_PATH),
        # quantization_config=quantization_config,
        dtype=_dtype,
        local_files_only=True,
        device_map=_device_map
    )

else:
    default_logger.info(f"Local model not found in {MODEL_LOCAL_PATH}. Downloading from HuggingFace...")

    os.makedirs(MODEL_LOCAL_PATH, exist_ok=True)

    processor: "Qwen3VLProcessor" = AutoProcessor.from_pretrained(DEFAULT_MODEL_NAME)   # type: ignore
    model: "GeneratableModel" = AutoModelForImageTextToText.from_pretrained(            # type: ignore
        DEFAULT_MODEL_NAME,
        # quantization_config=quantization_config,
        dtype=_dtype,
        device_map=_device_map
    )

    # Сохранить модель локально
    model.save_pretrained(str(MODEL_LOCAL_PATH))                    # type: ignore
    processor.save_pretrained(str(MODEL_LOCAL_PATH))                # type: ignore


processor = typing.cast("Qwen3VLProcessor", processor)
# model = typing.cast(TypedQwen3VL, model)