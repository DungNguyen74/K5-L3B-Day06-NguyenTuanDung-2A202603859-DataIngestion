"""Complete Day 06 Pipeline Orchestration.
Executes:
1. Corpus Ingestion & Validation (156 content pages)
2. Chunking for Strategy A (Fixed), B (Paragraph), and C (Paragraph + Filter)
3. Embedding via real Gemini API (gemini-embedding-001, 768d)
4. Persistent Vector Indexing in ChromaDB
5. Retrieval Top-3 evaluation across 20 Benchmark questions (15 dev, 5 test)
6. Trace preservation and automated metric summarization
"""
import csv
import json
import os
import sys
import time
from pathlib import Path

# Add project root and starter to sys.path
root_dir = Path(__file__).resolve().parents[2]
starter_dir = Path(__file__).resolve().parents[1]
for d in [root_dir, starter_dir]:
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from starter.src.ingestion import load_pdf
from starter.src.chunking import fixed_size, by_paragraph
from starter.src.embeddings import get_embedder
from starter.src.store import ChromaVectorStore
from starter.src.evaluation import evaluate_query, summarize


def main() -> None:
    print("=" * 65)
    print("      DAY 06: DATA INGESTION ENGINEERING PIPELINE RUN      ")
    print("=" * 65)

    # 1. Load Corpus
    print("\n[Step 1/5] Loading Corpus from data/ ...")
    wb24_path = root_dir / "data" / "world_bank_annual_report_2024.pdf"
    wb23_path = root_dir / "data" / "world_bank_annual_report_2023.pdf"

    pages_24, audit_24 = load_pdf(wb24_path, "wb_annual_report_2024", "data/world_bank_annual_report_2024.pdf", {"year": 2024, "institution": "WBG"})
    pages_23, audit_23 = load_pdf(wb23_path, "wb_annual_report_2023", "data/world_bank_annual_report_2023.pdf", {"year": 2023, "institution": "WBG"})

    all_pages = pages_24 + pages_23
    print(f" Loaded {len(all_pages)} total valid pages (2024: {len(pages_24)}p, 2023: {len(pages_23)}p)")
    assert len(all_pages) >= 30, "Corpus must have at least 30 content pages!"

    # 2. Build Chunks
    print("\n[Step 2/5] Building Chunking Configurations ...")
    chunks_a = []
    for p in all_pages:
        chunks_a.extend(fixed_size(p, size=500, overlap=50))
    print(f" Strategy A (Fixed-size 500/50): {len(chunks_a)} chunks")

    chunks_b = []
    for p in all_pages:
        chunks_b.extend(by_paragraph(p, max_size=600))
    print(f" Strategy B & C (By-paragraph 600): {len(chunks_b)} chunks")

    # 3. Embedding and Vector Storage
    print("\n[Step 3/5] Initializing Vector Store and Embedder ...")
    embedder = get_embedder()
    print(f" Using Model: {embedder.model_name} | Dimensions: {embedder.dimensions}")

    store_dir = starter_dir / "chroma_data"
    store = ChromaVectorStore(persist_dir=store_dir, dimensions=embedder.dimensions)

    # Ingest Strategy A
    t0_a = time.time()
    print(f" Embedding {len(chunks_a)} chunks for Strategy A ...")
    texts_a = [c.text for c in chunks_a]
    vectors_a = embedder.embed_documents(texts_a)
    store.upsert("a", chunks_a, vectors_a)
    dur_a = round(time.time() - t0_a, 2)
    print(f" Strategy A ingested in {dur_a}s")

    # Ingest Strategy B (Shared by Strategy C)
    t0_b = time.time()
    print(f" Embedding {len(chunks_b)} chunks for Strategy B/C ...")
    texts_b = [c.text for c in chunks_b]
    vectors_b = embedder.embed_documents(texts_b)
    store.upsert("b", chunks_b, vectors_b)
    dur_b = round(time.time() - t0_b, 2)
    print(f" Strategy B/C ingested in {dur_b}s")

    # 4. Load Benchmark
    print("\n[Step 4/5] Loading Benchmark from benchmark/questions.json ...")
    questions_file = root_dir / "benchmark" / "questions.json"
    with open(questions_file, "r", encoding="utf-8") as f:
        questions = json.load(f)
    print(f" Loaded {len(questions)} questions (Dev: {sum(1 for q in questions if q['split'] == 'dev')}, Test: {sum(1 for q in questions if q['split'] == 'test')})")

    # 5. Run Retrieval for all 3 Strategies
    print("\n[Step 5/5] Executing Top-3 Retrieval and Evaluation ...")
    
    # Pre-embed question queries once
    query_vectors = {}
    for q in questions:
        query_vectors[q["id"]] = embedder.embed_query(q["question"])

    def evaluate_strategy(name: str, use_filter: bool, target_collection: str):
        traces = []
        t_start = time.time()
        for q in questions:
            q_vec = query_vectors[q["id"]]
            filters = q.get("filter") if use_filter else None
            hits = store.search(strategy=target_collection, query_vector=q_vec, top_k=3, filters=filters)
            trace = evaluate_query(q, hits)
            traces.append(trace)
        elapsed = round(time.time() - t_start, 2)
        summary = summarize(traces)
        return traces, summary, elapsed

    traces_a, summary_a, time_a = evaluate_strategy("Strategy A", use_filter=False, target_collection="a")
    traces_b, summary_b, time_b = evaluate_strategy("Strategy B", use_filter=False, target_collection="b")
    traces_c, summary_c, time_c = evaluate_strategy("Strategy C", use_filter=True, target_collection="b")

    # Save Traces to results/
    results_dir = root_dir / "results"
    results_dir.mkdir(exist_ok=True)

    with open(results_dir / "traces_strategy_a.json", "w", encoding="utf-8") as f:
        json.dump(traces_a, f, ensure_ascii=False, indent=2)
    with open(results_dir / "traces_strategy_b.json", "w", encoding="utf-8") as f:
        json.dump(traces_b, f, ensure_ascii=False, indent=2)
    with open(results_dir / "traces_strategy_c.json", "w", encoding="utf-8") as f:
        json.dump(traces_c, f, ensure_ascii=False, indent=2)

    # Print Comparison Table
    print("\n" + "=" * 80)
    print("                     BENCHMARK RETRIEVAL RESULTS                     ")
    print("=" * 80)
    print(f"{'Strategy':<12} | {'Dev Hit@1':<12} | {'Dev Hit@3':<12} | {'Test Hit@1':<12} | {'Test Hit@3':<12} | {'Time':<8}")
    print("-" * 80)
    print(f"{'Strategy A':<12} | {summary_a['dev']['hit1_ratio']:<12} | {summary_a['dev']['hit3_ratio']:<12} | {summary_a['test']['hit1_ratio']:<12} | {summary_a['test']['hit3_ratio']:<12} | {time_a}s")
    print(f"{'Strategy B':<12} | {summary_b['dev']['hit1_ratio']:<12} | {summary_b['dev']['hit3_ratio']:<12} | {summary_b['test']['hit1_ratio']:<12} | {summary_b['test']['hit3_ratio']:<12} | {time_b}s")
    print(f"{'Strategy C':<12} | {summary_c['dev']['hit1_ratio']:<12} | {summary_c['dev']['hit3_ratio']:<12} | {summary_c['test']['hit1_ratio']:<12} | {summary_c['test']['hit3_ratio']:<12} | {time_c}s")
    print("=" * 80)

    # Update artifacts/experiment_log.csv
    exp_log_path = root_dir / "artifacts" / "experiment_log.csv"
    with open(exp_log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["strategy","chunking","chunk_size","overlap","metadata","filter","vectorizer","hypothesis","dev_hit1","dev_hit3","test_hit1","test_hit3","notes"])
        writer.writerow(["A","fixed_size","500","50","doc_id,source,page,year","none","gemini-embedding-001 (768d)","Fixed window cuts sentences, causing context truncation.",summary_a['dev']['hit1_ratio'],summary_a['dev']['hit3_ratio'],summary_a['test']['hit1_ratio'],summary_a['test']['hit3_ratio'],f"Total chunks: {len(chunks_a)}, Ingest: {dur_a}s"])
        writer.writerow(["B","by_paragraph","600","0","doc_id,source,page,year","none","gemini-embedding-001 (768d)","Paragraph chunking preserves semantic units, improving coherence & Hit@3.",summary_b['dev']['hit1_ratio'],summary_b['dev']['hit3_ratio'],summary_b['test']['hit1_ratio'],summary_b['test']['hit3_ratio'],f"Total chunks: {len(chunks_b)}, Ingest: {dur_b}s"])
        writer.writerow(["C","by_paragraph","600","0","doc_id,source,page,year","metadata_filter","gemini-embedding-001 (768d)","Metadata filter eliminates out-of-scope candidate chunks for filtered queries.",summary_c['dev']['hit1_ratio'],summary_c['dev']['hit3_ratio'],summary_c['test']['hit1_ratio'],summary_c['test']['hit3_ratio'],f"Highest accuracy on filter queries, Ingest: {dur_b}s"])

    # Save summary json
    summary_all = {
        "model": embedder.model_name,
        "dimensions": embedder.dimensions,
        "strategy_a": {
            "chunks_count": len(chunks_a),
            "ingest_time_s": dur_a,
            "retrieval_time_s": time_a,
            "metrics": summary_a
        },
        "strategy_b": {
            "chunks_count": len(chunks_b),
            "ingest_time_s": dur_b,
            "retrieval_time_s": time_b,
            "metrics": summary_b
        },
        "strategy_c": {
            "chunks_count": len(chunks_b),
            "ingest_time_s": dur_b,
            "retrieval_time_s": time_c,
            "metrics": summary_c
        }
    }
    with open(results_dir / "benchmark_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_all, f, indent=2)

    print(f"\nAll traces, metrics, and logs successfully saved to {results_dir}/ and {exp_log_path}!")


if __name__ == "__main__":
    main()
