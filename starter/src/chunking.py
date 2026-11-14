"""Implement fixed-size and structure-aware chunking.
Provides deterministic chunk generation, stable IDs, and full metadata preservation.
"""
import re
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int = 500, overlap: int = 50) -> list[Chunk]:
    """Split text into overlapping windows of fixed character length while preserving metadata."""
    text = page.text.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    
    # If text is smaller than size, return a single chunk
    if len(text) <= size:
        chunk_id = f"{page.document_id}_p{page.page}_fix0"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=text,
                metadata={**page.metadata, "chunk_strategy": "fixed_size", "chunk_index": 0}
            )
        )
        return chunks

    step = size - overlap
    idx = 0
    start = 0

    while start < len(text):
        end = min(start + size, len(text))
        chunk_text = text[start:end].strip()
        
        if chunk_text:
            chunk_id = f"{page.document_id}_p{page.page}_fix{idx}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=chunk_text,
                    metadata={**page.metadata, "chunk_strategy": "fixed_size", "chunk_index": idx}
                )
            )
            idx += 1
            
        if end >= len(text):
            break
        start += step

    return chunks


def by_paragraph(page: DocumentPage, max_size: int = 600) -> list[Chunk]:
    """Group paragraphs, split oversized paragraphs cleanly, and retain full page metadata."""
    text = page.text.strip()
    if not text:
        return []

    # Split by natural paragraph breaks
    raw_paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not raw_paras:
        raw_paras = [text]

    # Sub-split any paragraph that exceeds max_size by sentence boundaries
    normalized_paras: list[str] = []
    for p in raw_paras:
        if len(p) <= max_size:
            normalized_paras.append(p)
        else:
            # Split by sentence end punctuation (. ! ?)
            sentences = re.split(r"(?<=[.!?])\s+", p)
            current_sent_chunk = ""
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                if not current_sent_chunk:
                    current_sent_chunk = s
                elif len(current_sent_chunk) + len(s) + 1 <= max_size:
                    current_sent_chunk += " " + s
                else:
                    normalized_paras.append(current_sent_chunk)
                    current_sent_chunk = s
            if current_sent_chunk:
                normalized_paras.append(current_sent_chunk)

    # Greedily group consecutive small paragraphs up to max_size
    chunks: list[Chunk] = []
    current_text = ""
    idx = 0

    for para in normalized_paras:
        if not current_text:
            current_text = para
        elif len(current_text) + len(para) + 2 <= max_size:
            current_text += "\n\n" + para
        else:
            chunk_id = f"{page.document_id}_p{page.page}_para{idx}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=current_text,
                    metadata={**page.metadata, "chunk_strategy": "by_paragraph", "chunk_index": idx}
                )
            )
            idx += 1
            current_text = para

    if current_text:
        chunk_id = f"{page.document_id}_p{page.page}_para{idx}"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=current_text,
                metadata={**page.metadata, "chunk_strategy": "by_paragraph", "chunk_index": idx}
            )
        )

    return chunks
