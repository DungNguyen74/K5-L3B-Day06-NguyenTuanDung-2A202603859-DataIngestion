"""Setup verification script for Day 06 Data Ingestion Engineering.
Validates:
1. Python environment and libraries
2. Vector Store persistence (ChromaDB)
3. Embedding Model (Gemini API text-embedding-004 or Local ONNX)
4. Cosine similarity and metadata filtering
"""
import os
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Ensure root and starter are in sys.path
root_dir = Path(__file__).resolve().parents[2]
starter_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(starter_dir) not in sys.path:
    sys.path.insert(0, str(starter_dir))

env_path = starter_dir / '.env'
load_dotenv(env_path)

print("=== DAY 06 SETUP VERIFICATION ===")
print(f"Python version: {sys.version.split()[0]}")

provider = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()
gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

print(f"Embedding Provider: {provider.upper()}")

if provider == "gemini":
    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        print("\n[!] CHÚ Ý: Chưa tìm thấy GEMINI_API_KEY trong starter/.env")
        print("    -> Bạn hãy mở file starter/.env và dán key vào dòng: GEMINI_API_KEY=AIzaSy...")
        print("    -> Sau đó chạy lại: python starter/scripts/check_setup.py\n")
        sys.exit(1)
    
    try:
        from starter.src.embeddings import GeminiEmbedder
        embedder = GeminiEmbedder(api_key=gemini_key, model_name=os.getenv("EMBEDDING_MODEL", "text-embedding-004"))
        vec = embedder.embed_query("Kiểm tra kết nối Gemini API embedding")
        print(f"Gemini API Embedding: SUCCESS | Model: {embedder.model_name} | Dimensions: {len(vec)}")
    except Exception as e:
        sys.exit(f"Lỗi kết nối Gemini API: {e}")
else:
    from starter.src.embeddings import LocalEmbedder
    embedder = LocalEmbedder()
    vec = embedder.embed_query("Kiểm tra embedding local")
    print(f"Local Embedding: SUCCESS | Model: {embedder.model_name} | Dimensions: {len(vec)}")

# Test Vector Store
try:
    import chromadb
    test_dir = Path(__file__).resolve().parents[1] / 'test_check_chroma_db'
    client = chromadb.PersistentClient(path=str(test_dir))
    
    col = client.get_or_create_collection(name="check_col", metadata={"hnsw:space": "cosine"})
    col.upsert(
        ids=["c1", "c2"],
        documents=["Quy chế đào tạo 2024", "Quy chế học bổng 2023"],
        embeddings=[embedder.embed_query("Quy chế đào tạo 2024"), embedder.embed_query("Quy chế học bổng 2023")],
        metadatas=[{"year": 2024, "section": "dao_tao"}, {"year": 2023, "section": "hoc_bong"}]
    )
    
    query_vec = embedder.embed_query("quy chế đào tạo")
    res = col.query(query_embeddings=[query_vec], n_results=1, where={"year": 2024})
    assert len(res["ids"][0]) == 1 and res["ids"][0][0] == "c1", "Metadata filtering test failed"
    
    del client
    shutil.rmtree(test_dir, ignore_errors=True)
    print("Vector Store (Chroma Persistent Client) & Cosine Filter: VERIFIED")
except Exception as e:
    sys.exit(f"Lỗi Vector Store: {e}")

print("\nSetup OK. Sẵn sàng cho Corpus Ingestion và Benchmark!")
