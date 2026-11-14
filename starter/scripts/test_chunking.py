"""Checkpoint 1:50 Verification Script:
Reads corpus, normalizes text, generates both chunk configurations (Fixed vs Paragraph),
computes length distributions, and exports chunk samples to results/.
"""
import json
import statistics
import sys
from pathlib import Path

# Add root to sys.path
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from starter.src.ingestion import load_pdf
from starter.src.chunking import fixed_size, by_paragraph

# 1. Load documents
wb24_pages, audit_24 = load_pdf(
    root_dir / 'data' / 'world_bank_annual_report_2024.pdf',
    'wb_annual_report_2024',
    'data/world_bank_annual_report_2024.pdf',
    {'year': 2024, 'publisher': 'World Bank'}
)
wb23_pages, audit_23 = load_pdf(
    root_dir / 'data' / 'world_bank_annual_report_2023.pdf',
    'wb_annual_report_2023',
    'data/world_bank_annual_report_2023.pdf',
    {'year': 2023, 'publisher': 'World Bank'}
)

all_pages = wb24_pages + wb23_pages
print(f"=== CHECKPOINT 1:50: CHUNKING TEST ===")
print(f"Total valid content pages loaded: {len(all_pages)}")
print(f"- 2024 Report: {len(wb24_pages)} pages")
print(f"- 2023 Report: {len(wb23_pages)} pages (skipped empty/divider pages: {audit_23['empty_or_skipped_pages']})")

# 2. Generate Configuration A: Fixed-size (500 chars, overlap 50)
chunks_a = []
for p in all_pages:
    chunks_a.extend(fixed_size(p, size=500, overlap=50))

# 3. Generate Configuration B/C: By-paragraph (max 600 chars)
chunks_b = []
for p in all_pages:
    chunks_b.extend(by_paragraph(p, max_size=600))

# 4. Statistical Analysis
def get_stats(chunks, name):
    lengths = [len(c.text) for c in chunks]
    return {
        "strategy": name,
        "total_chunks": len(chunks),
        "total_chars": sum(lengths),
        "avg_length": round(statistics.mean(lengths), 1),
        "median_length": round(statistics.median(lengths), 1),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "stdev_length": round(statistics.stdev(lengths), 1) if len(lengths) > 1 else 0
    }

stats_a = get_stats(chunks_a, "Strategy A (Fixed-size 500/50)")
stats_b = get_stats(chunks_b, "Strategy B/C (By-paragraph 600)")

print("\n--- Thống kê cấu hình Chunk ---")
for s in [stats_a, stats_b]:
    print(f"\n{s['strategy']}:")
    print(f"  - Tổng số chunk: {s['total_chunks']}")
    print(f"  - Độ dài trung bình: {s['avg_length']} ký tự (Median: {s['median_length']}, Min: {s['min_length']}, Max: {s['max_length']})")
    print(f"  - Độ lệch chuẩn độ dài: {s['stdev_length']}")

# 5. Export samples and audit results to results/
results_dir = root_dir / 'results'
results_dir.mkdir(exist_ok=True)

with open(results_dir / 'chunking_stats.json', 'w', encoding='utf-8') as f:
    json.dump({"stats_a": stats_a, "stats_b": stats_b, "audit_24": audit_24, "audit_23": audit_23}, f, indent=2)

# Export first 5 sample chunks of each
with open(results_dir / 'samples_strategy_a.json', 'w', encoding='utf-8') as f:
    json.dump([{"chunk_id": c.chunk_id, "page": c.page, "year": c.metadata.get("year"), "text": c.text} for c in chunks_a[:5]], f, ensure_ascii=False, indent=2)

with open(results_dir / 'samples_strategy_b.json', 'w', encoding='utf-8') as f:
    json.dump([{"chunk_id": c.chunk_id, "page": c.page, "year": c.metadata.get("year"), "text": c.text} for c in chunks_b[:5]], f, ensure_ascii=False, indent=2)

print(f"\nSaved chunking statistics and samples to {results_dir.relative_to(root_dir)}/")
print("Checkpoint 1:50 OK!")
