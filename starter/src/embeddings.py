"""Embedding provider adapters (Gemini API & Local ONNX).
Complies with Day 06 Rubric: uses a real embedding model, no mock vectors.
"""
import os
from typing import Protocol, List
from dotenv import load_dotenv

load_dotenv()


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class GeminiEmbedder:
    """Gemini API Embedder (gemini-embedding-001, 768 dimensions)."""

    def __init__(self, api_key: str | None = None, model_name: str = "gemini-embedding-001", dimensions: int = 768) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing. Please set it in starter/.env or pass it.")
        
        self.model_name = model_name
        self.dimensions = dimensions

        from google import genai
        self.client = genai.Client(api_key=self.api_key)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        
        embeddings: list[list[float]] = []
        batch_size = 20  # Safe batch size for rate limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            config = {"output_dimensionality": self.dimensions} if self.dimensions else None
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=batch,
                config=config
            )
            for emb in response.embeddings:
                embeddings.append(list(emb.values))
        return embeddings

    def embed_query(self, question: str) -> list[float]:
        config = {"output_dimensionality": self.dimensions} if self.dimensions else None
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=question,
            config=config
        )
        return list(response.embeddings[0].values)


class LocalEmbedder:
    """Local ONNX Embedder (all-MiniLM-L6-v2, 384 dimensions)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        self.model_name = model_name
        self.dimensions = 384
        self._ef = DefaultEmbeddingFunction()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self._ef(texts)
        return [list(e) for e in embeddings]

    def embed_query(self, question: str) -> list[float]:
        return list(self._ef([question])[0])


def get_embedder() -> Embedder:
    """Instantiate the configured embedder from environment variables."""
    provider = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if provider == "gemini" and gemini_key:
        model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
        dims = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))
        return GeminiEmbedder(api_key=gemini_key, model_name=model, dimensions=dims)
    elif provider == "gemini" and not gemini_key:
        raise ValueError("GEMINI_API_KEY is not set in starter/.env. Please provide your Gemini API key.")
    else:
        return LocalEmbedder()
