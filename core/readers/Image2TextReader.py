import typing
import torch

from core.chunking import create_chunks_with_coords
from core.readers.BaseChunkReader import BaseChunkReader
from core.types import TChunk
from PIL import Image
from transformers import BatchFeature

if typing.TYPE_CHECKING:
    from transformers import Qwen3VLProcessor
    from core.types import GeneratableModel

TMessagesObject = list[dict[str, typing.Any]]

class Image2TextReader(BaseChunkReader):
    """Ридер для чтения сюжетов в изображениях."""

    def __init__(
        self,
        filepath: str,
        model: "GeneratableModel",
        processor: "Qwen3VLProcessor",
    ):
        self.filepath = filepath
        self._text: str = ""
        self._loaded = False
        self.processor = processor
        self.model = model


    def load(self) -> None:
        if self._loaded:
            return

        image = Image.open(self.filepath).convert("RGB")

        # Resizes the longest side to 1024px in-place
        image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

        messages_object: TMessagesObject = [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": image,
                },
                {
                    "type": "text",
                    # "text": "Describe what you see in detail.",
                    "text": (""
                        + "Подробно опиши увиденное."
                        + " Если совершается действие, назови его."
                        + " Если присутствует текст, прочитай его."
                        + " Ответ на русском не более 200 символов."
                    ),
                },
            ]
        }]

        prompt: str = self.processor.apply_chat_template( # type: ignore
            messages_object,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )

        # 5. Preprocess inputs
        inputs: BatchFeature = self.processor(text=[prompt], images=[image], return_tensors="pt") # type: ignore

        # The framework shifts individual layers to the GPU; map the inputs accordingly
        inputs: BatchFeature = typing.cast(BatchFeature, inputs.to(self.model.device)) # type: ignore

        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=200,

                # pad_token_id=self.processor.tokenizer.eos_token_id,  # Add this line

                # max_new_tokens=150,
                # max_new_tokens=40,

                # temperature=0.7,   # Recommended for non-thinking vision tasks
                # top_p=0.80,        # Narrows down selection criteria
                # top_k=20,
                # min_p=0.0,

                # bad_words_ids=[think_id],  # Block reasoning blocks
            )

        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
        ]

        output_text: list[str] = self.processor.batch_decode( # type: ignore
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
            enable_thinking=False,
        )

        self._text = output_text[0]

        self._loaded = True


    def is_loaded(self) -> bool:
        return self._loaded


    def _chars_with_coords(self) -> typing.Iterator[tuple[str, tuple[int]]]:
        self.load()

        for char_idx, char in enumerate(self._text):
            yield char, (char_idx,)


    def getChunk(self, from_: list[int], to: list[int]) -> TChunk:
        self.load()

        start   = from_[0]
        end     = to[0] + 1  # включительно
        text    = self._text[start:end]

        return {
            "text": text,
            "from": from_,
            "to": to,
        }


    def createChunksIterator(self) -> typing.Iterator[TChunk]:
        return create_chunks_with_coords(
            self._chars_with_coords(),
            delimiters=[" "]
        )


    def createChunks(self) -> list[TChunk]:
        return [chunk for chunk in self.createChunksIterator()]