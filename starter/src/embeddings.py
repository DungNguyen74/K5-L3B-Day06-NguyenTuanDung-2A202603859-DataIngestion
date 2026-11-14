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
    """Gemini API Embedder (text-embedding-004, 768 dimensions)."""

    def __init__(self, api_key: str | None = None, model_name: str = "text-embedding-004") -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing. Please set it in starter/.env or pass it.")
        
        self.model_name = model_name
        self.dimensions = 768

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self._use_new_sdk = True
        except ImportError:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=self.api_key)
            self.client = genai_legacy
            self._use_new_sdk = False

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        
        embeddings: list[list[float]] = []
        batch_size = 20  # Safe batch size for Gemini API rate limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            if self._use_new_sdk:
                response = self.client.models.embed_content(
                    model=self.model_name,
                    contents=batch
                )
                for emb in response.embeddings:
                    embeddings.append(list(emb.values))
            else:
                for text in batch:
                    res = self.client.embed_content(
                        model=f"models/{self.model_name}" if not self.model_name.startswith("models/") else self.model_name,
                        content=text
                    )
                    embeddings.append(list(res["embedding"]))
        return embeddings

    def embed_query(self, question: str) -> list[float]:
        if self._use_new_sdk:
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=question
            )
            return list(response.embeddings[0].values)
        else:
            res = self.client.embed_content(
                model=f"models/{self.model_name}" if not self.model_name.startswith("models/") else self.model_name,
                content=question
            )
            return list(res["embedding"])


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
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        return GeminiEmbedder(api_key=gemini_key, model_name=model)
    elif provider == "gemini" and not gemini_key:
        raise ValueError("GEMINI_API_KEY is not set in starter/.env. Please provide your Gemini API key.")
    else:
        return LocalEmbedder()
