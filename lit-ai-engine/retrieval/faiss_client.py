"""
faiss_client.py - FAISS search layer
"""

import os
import json
import faiss
import torch
import numpy as np
from sentence_transformers import SentenceTransformer

# ========= PATH =========
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAISS_DIR = os.path.join(BASE_DIR, "faiss_store")

FAISS_INDEX_PATH = os.path.join(FAISS_DIR, "books.index")
FAISS_IDS_PATH = os.path.join(FAISS_DIR, "books_ids.json")

# ========= GLOBALS =========
_index = None
_ids = None
_model = None


# ========= LOAD FAISS =========
def load_faiss():
    global _index, _ids

    if _index is not None:
        return _index, _ids

    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError("❌ FAISS index not found")

    _index = faiss.read_index(FAISS_INDEX_PATH)

    with open(FAISS_IDS_PATH, "r", encoding="utf-8") as f:
        _ids = json.load(f)

    print(f"✅ FAISS loaded: {_index.ntotal}")

    return _index, _ids


# ========= LOAD MODEL =========
def get_model():
    global _model

    if _model is not None:
        return _model

    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"🧠 Loading model on {device}...")

    _model = SentenceTransformer(
        "all-mpnet-base-v2",
        device=device
    )

    _model.max_seq_length = 256

    return _model


# ========= SEARCH =========
def search(query: str, top_k: int = 10):

    if not query.strip():
        return []

    index, ids = load_faiss()
    model = get_model()

    vec = model.encode(
        [query],
        normalize_embeddings=True
    )

    vec = np.array(vec, dtype="float32")
    faiss.normalize_L2(vec)

    distances, indices = index.search(vec, top_k)

    results = []

    for score, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue

        results.append({
            "book_id": str(ids[idx]).strip(),
            "score": float(score)
        })

    return results