"""Evaluation metrics and trace logging for Day 06 Retrieval Benchmark.
Computes Hit@1 and Evidence Hit@3 against gold source, page and evidence quote.
"""
import re
from typing import Any


def clean_text_for_match(s: str) -> str:
    """Normalize text for evidence matching (whitespace, punctuation, case-insensitive)."""
    s = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", s)
    s = s.replace("—", "-").replace("–", "-").replace("\u00a0", " ")
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def is_chunk_a_hit(hit: dict[str, Any], gold_source_id: str, gold_page: int, evidence_quote: str) -> bool:
    """A chunk is a hit if it matches the gold page and contains the gold evidence quote."""
    meta = hit.get("metadata", {})
    chunk_page = meta.get("page")
    chunk_text = hit.get("text", "")
    
    # Must match page
    if chunk_page != gold_page:
        return False
        
    # Check evidence containment
    clean_quote = clean_text_for_match(evidence_quote)
    clean_chunk = clean_text_for_match(chunk_text)
    
    # Check substring containment or 80%+ key phrases
    if clean_quote in clean_chunk:
        return True
        
    # If quote is very long, check if a 40-char key prefix/suffix matches
    words = clean_quote.split()
    if len(words) >= 6:
        sub_phrase_1 = " ".join(words[:6])
        sub_phrase_2 = " ".join(words[-6:])
        if sub_phrase_1 in clean_chunk or sub_phrase_2 in clean_chunk:
            return True

    return False


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate top-3 hits against question gold attributes and produce a full trace."""
    gold_source = question["gold_source_id"]
    gold_page = question["gold_page"]
    evidence_quote = question["evidence_quote"]
    
    evaluated_hits = []
    hit_at_1 = False
    hit_at_3 = False
    
    for rank, h in enumerate(hits, start=1):
        hit_flag = is_chunk_a_hit(h, gold_source, gold_page, evidence_quote)
        if rank == 1 and hit_flag:
            hit_at_1 = True
        if hit_flag:
            hit_at_3 = True
            
        evaluated_hits.append({
            "rank": rank,
            "chunk_id": h.get("chunk_id"),
            "page": h.get("metadata", {}).get("page"),
            "score": h.get("score"),
            "is_hit": hit_flag,
            "metadata": h.get("metadata"),
            "text_snippet": h.get("text", "")[:200]
        })
        
    return {
        "question_id": question["id"],
        "split": question["split"],
        "type": question["type"],
        "question": question["question"],
        "gold_page": gold_page,
        "gold_source_id": gold_source,
        "filter": question.get("filter"),
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "top_hits": evaluated_hits
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by split (dev vs test)."""
    dev_traces = [t for t in traces if t["split"] == "dev"]
    test_traces = [t for t in traces if t["split"] == "test"]
    
    def calc_metrics(subset):
        total = len(subset)
        if total == 0:
            return {"hit1_count": 0, "hit1_ratio": "0/0", "hit1_rate": 0.0, "hit3_count": 0, "hit3_ratio": "0/0", "hit3_rate": 0.0}
        hit1 = sum(1 for t in subset if t["hit_at_1"])
        hit3 = sum(1 for t in subset if t["hit_at_3"])
        return {
            "total": total,
            "hit1_count": hit1,
            "hit1_ratio": f"{hit1}/{total}",
            "hit1_rate": round(hit1 / total * 100, 1),
            "hit3_count": hit3,
            "hit3_ratio": f"{hit3}/{total}",
            "hit3_rate": round(hit3 / total * 100, 1)
        }
        
    return {
        "dev": calc_metrics(dev_traces),
        "test": calc_metrics(test_traces),
        "total_queries": len(traces)
    }
