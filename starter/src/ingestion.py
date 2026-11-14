"""Read and normalize source data.
Extracts physical pages, logs empty/skipped pages, applies Unicode normalization.
Traceability back to document_id, source and physical page number is strictly preserved.
"""
import json
import re
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from .models import DocumentPage


def normalize_text(text: str) -> str:
    """Normalize Unicode (NFC) and whitespace while retaining paragraph boundaries."""
    if not text:
        return ""
    # Unicode NFC normalization
    normalized = unicodedata.normalize("NFC", text)
    # Replace non-breaking spaces and irregular tabs
    normalized = normalized.replace("\u00a0", " ").replace("\u200b", "")
    # Normalize horizontal whitespace
    normalized = re.sub(r"[ \t]+", " ", normalized)
    # Normalize multiple newlines into standard paragraph breaks (\n\n)
    normalized = re.sub(r"\r\n|\r", "\n", normalized)
    normalized = re.sub(r"\n\s*\n+", "\n\n", normalized)
    return normalized.strip()


def load_pdf(path: Path, document_id: str, source: str, default_metadata: dict | None = None) -> list[DocumentPage]:
    """Extract physical pages from PDF, log empty pages, and return DocumentPage instances."""
    reader = PdfReader(str(path))
    pages: list[DocumentPage] = []
    default_metadata = default_metadata or {}
    
    empty_pages: list[int] = []
    
    for idx, page_obj in enumerate(reader.pages):
        physical_page_num = idx + 1
        raw_text = page_obj.extract_text() or ""
        clean_text = normalize_text(raw_text)
        
        if not clean_text or len(clean_text) < 20:
            empty_pages.append(physical_page_num)
            continue
            
        page_meta = dict(default_metadata)
        page_meta["physical_page"] = physical_page_num
        page_meta["char_count"] = len(clean_text)
        
        pages.append(
            DocumentPage(
                document_id=document_id,
                source=source,
                page=physical_page_num,
                text=clean_text,
                metadata=page_meta
            )
        )
        
    audit_log = {
        "document_id": document_id,
        "source": source,
        "total_physical_pages": len(reader.pages),
        "valid_extracted_pages": len(pages),
        "empty_or_skipped_pages": empty_pages
    }
    
    return pages, audit_log
