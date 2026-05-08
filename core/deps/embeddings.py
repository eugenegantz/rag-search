import chromadb
from transformers import pipeline, AutoModel, AutoTokenizer

DEFAULT_MODEL_NAME = "intfloat/multilingual-e5-large"
DEFAULT_DB_PATH = "./db"
DEFAULT_COLLECTION_NAME = "rag_search"

model       = AutoModel.from_pretrained("./models/" + DEFAULT_MODEL_NAME, local_files_only=True)  # type: ignore
tokenizer   = AutoTokenizer.from_pretrained("./models/" + DEFAULT_MODEL_NAME, local_files_only=True)  # type: ignore
pipe        = pipeline("feature-extraction", model=model, tokenizer=tokenizer)  # type: ignore
db          = chromadb.PersistentClient(path=DEFAULT_DB_PATH)