"""
faiss_client.py - Clean FAISS loader for RAG
"""

import os
import json
import faiss
import torch
from sentence_transformers import SentenceTransformer

# ================= PATH SETUP =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAISS_DIR = os.path.join(BASE_DIR, "faiss_store")

# Production override
FAISS_DIR = os.environ.get("FAISS_PERSIST_DIR", FAISS_DIR)

FAISS_INDEX_PATH = os.path.join(FAISS_DIR, "books.index")
FAISS_IDS_PATH = os.path.join(FAISS_DIR, "books_ids.json")

print(f"📂 FAISS DIR: {FAISS_DIR}")


# ================= GLOBALS =================
_index = None
_ordered_ids = None
_model = None


# ================= LOAD FAISS =================
def load_faiss():
    global _index, _ordered_ids

    if _index is not None:
        return _index, _ordered_ids

    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError(f"❌ FAISS index not found at {FAISS_INDEX_PATH}")

    print("⚡ Loading FAISS index...")

    _index = faiss.read_index(FAISS_INDEX_PATH)

    with open(FAISS_IDS_PATH, "r", encoding="utf-8") as f:
        _ordered_ids = json.load(f)

    print(f"✅ FAISS loaded: {_index.ntotal} vectors")

    return _index, _ordered_ids


# ================= LOAD MODEL =================
def get_model():
    global _model

    if _model is not None:
        return _model

    print("🔄 Loading embedding model: all-mpnet-base-v2")

    # ✅ auto GPU detection
    device = "cuda" if torch.cuda.is_available() else "cpu"

    _model = SentenceTransformer(
        "all-mpnet-base-v2",
        device=device
    )

    # ✅ fix sequence length
    _model.max_seq_length = 256

    print(f"✅ Model loaded on {device}")

    return _model


# ================= SEARCH =================
def search(query: str, top_k: int = 10):
    """
    Pure FAISS search → returns book_ids + scores
    """

    if not query.strip():
        return []

    index, ordered_ids = load_faiss()
    model = get_model()

    # encode query
    vec = model.encode(
        [query],
        normalize_embeddings=True
    )

    vec = vec.astype("float32")
    faiss.normalize_L2(vec)

    distances, indices = index.search(vec, top_k)

    results = []

    for score, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue

        book_id = str(ordered_ids[idx]).strip()

        results.append({
            "book_id": book_id,
            "score": float(score)
        })

    return results


# ================= STATS =================
def get_collection_stats():
    try:
        index, _ = load_faiss()
        return {
            "total_embeddings": index.ntotal,
            "backend": "FAISS",
            "has_data": index.ntotal > 0
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_embeddings": 0,
            "has_data": False
        }