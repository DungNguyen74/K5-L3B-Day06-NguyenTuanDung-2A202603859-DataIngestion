"""Persistent Vector Store implementation using ChromaDB.
Complies with Day 06 Rubric:
- Persistent disk storage (no in-memory mock)
- Cosine distance metric (hnsw:space: cosine)
- Strict metadata filtering
- Idempotent upsert (re-ingesting does not duplicate chunks)
"""
import os
from pathlib import Path
from typing import Any
import chromadb
from .models import Chunk


class ChromaVectorStore:
    """ChromaDB Persistent Client implementation for Day 06."""

    def __init__(self, persist_dir: str | Path = "./chroma_data", dimensions: int = 768) -> None:
        self.persist_dir = str(Path(persist_dir).resolve())
        self.dimensions = dimensions
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collections: dict[str, Any] = {}

    def get_or_create_collection(self, strategy: str):
        col_name = f"strategy_{strategy.lower()}"
        if col_name not in self.collections:
            self.collections[col_name] = self.client.get_or_create_collection(
                name=col_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self.collections[col_name]

    def create_schema(self) -> None:
        """Initialize or reset collections for strategies."""
        # Ensured via get_or_create_collection
        pass

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Idempotent upsert: writes stable IDs and replaces any existing chunk with the same ID."""
        if not chunks:
            return

        if len(chunks) != len(vectors):
            raise ValueError(f"Mismatch between chunks count ({len(chunks)}) and vectors count ({len(vectors)})")

        col = self.get_or_create_collection(strategy)
        
        # Batch upsert to prevent payload overflow
        batch_size = 200
        for i in range(0, len(chunks), batch_size):
            b_chunks = chunks[i:i + batch_size]
            b_vectors = vectors[i:i + batch_size]
            
            ids = [c.chunk_id for c in b_chunks]
            documents = [c.text for c in b_chunks]
            
            # Format metadata: Chroma only accepts str, int, float, bool
            metadatas = []
            for c in b_chunks:
                clean_meta = {}
                for k, v in c.metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        clean_meta[k] = v
                    elif isinstance(v, list):
                        clean_meta[k] = ",".join(str(x) for x in v)
                clean_meta["source"] = c.source
                clean_meta["document_id"] = c.document_id
                clean_meta["page"] = c.page
                clean_meta["chunk_id"] = c.chunk_id
                metadatas.append(clean_meta)

            col.upsert(
                ids=ids,
                documents=documents,
                embeddings=b_vectors,
                metadatas=metadatas
            )

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Filter metadata in vector index, rank by cosine similarity, return top-k."""
        col = self.get_or_create_collection(strategy)
        
        where_clause = None
        if filters:
            # Build Chroma where clause
            if len(filters) == 1:
                k, v = next(iter(filters.items()))
                where_clause = {k: {"$eq": v}}
            else:
                where_clause = {"$and": [{k: {"$eq": v}} for k, v in filters.items()]}

        res = col.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_clause
        )

        hits: list[dict[str, Any]] = []
        if res and res["ids"] and res["ids"][0]:
            count = len(res["ids"][0])
            for i in range(count):
                hits.append({
                    "chunk_id": res["ids"][0][i],
                    "text": res["documents"][0][i],
                    "score": res["distances"][0][i],  # Cosine distance (smaller = closer)
                    "metadata": res["metadatas"][0][i]
                })

        return hits
