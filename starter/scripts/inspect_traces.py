import json

with open("results/traces_strategy_b.json", "r", encoding="utf-8") as f:
    traces = json.load(f)

for t in traces:
    print(f"[{t['question_id']}] {t['question'][:50]}... | Gold: p{t['gold_page']}")
    for h in t["top_hits"]:
        print(f"   Rank {h['rank']} -> Page {h['page']} (dist {round(h['score'], 3)}) Hit: {h['is_hit']} | Text: {h['text_snippet'][:80]}...")
