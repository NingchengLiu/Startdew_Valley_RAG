from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / ".env")

from openai import OpenAI
import os
from langchain.embeddings.base import Embeddings

A2_BASE_URL = os.getenv("A2_BASE_URL", "https://rsm-8430-a2.bjlkeng.io")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
BATCH_SIZE = 100


class LocalEmbedder:
    def __init__(self):
        self._client = OpenAI(base_url=A2_BASE_URL, api_key=LLM_API_KEY)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        all_embeddings = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            response = self._client.embeddings.create(
                input=batch,
                model=EMBEDDING_MODEL,
            )
            all_embeddings.extend([item.embedding for item in response.data])
        return all_embeddings


class LocalEmbeddingsWrapper(Embeddings):
    def __init__(self, embedder: LocalEmbedder):
        self.embedder = embedder

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embedder.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        # BGE models need a prefix for queries only
        prefixed = BGE_QUERY_PREFIX + text
        response = self.embedder._client.embeddings.create(
            input=[prefixed],
            model=EMBEDDING_MODEL,
        )
        return response.data[0].embedding


def build_embeddings() -> LocalEmbeddingsWrapper:
    return LocalEmbeddingsWrapper(LocalEmbedder())

embeddings = build_embeddings()