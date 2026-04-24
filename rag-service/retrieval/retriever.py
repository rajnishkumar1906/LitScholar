"""
retriever.py - Book retrieval using FAISS
"""

from sentence_transformers import SentenceTransformer
from retrieval.faiss_client import get_faiss_collection
import os
import numpy as np

# Global model instance
_model = None

# ✅ Use similarity threshold instead of "distance"
MIN_SIMILARITY = float(os.environ.get('FAISS_MIN_SIMILARITY', '0.35'))


def get_model():
    """Get or load the sentence transformer model"""
    global _model

    if _model is None:
        print("🔄 Loading embedding model: all-mpnet-base-v2")

        device = os.environ.get('MODEL_DEVICE', 'cpu')

        _model = SentenceTransformer(
            "all-mpnet-base-v2",
            device=device,
            cache_folder=os.environ.get('MODEL_CACHE_DIR', "/tmp/model_cache")
        )

        if os.environ.get('USE_FP16', 'false').lower() == 'true':
            try:
                _model.half()
                print("✅ Using FP16 precision")
            except:
                print("⚠️ FP16 not supported")

        print("✅ Embedding model loaded successfully")

    return _model


def search_books(query: str, top_k: int = 6, min_score: float | None = None):
    """
    Search for books using FAISS semantic similarity
    """

    if not query or not query.strip():
        print("⚠️ Empty query provided")
        return []

    if top_k < 1:
        top_k = 6

    try:
        faiss_data = get_faiss_collection()
        index = faiss_data["index"]
        ordered_ids = faiss_data["ordered_ids"]
    except Exception as e:
        print(f"❌ FAISS collection error: {e}")
        return []

    try:
        model = get_model()

        query_embedding = model.encode(
            query,
            normalize_embeddings=True
        )

        query_embedding_np = np.array([query_embedding], dtype="float32")

        distances, indices = index.search(query_embedding_np, top_k)

    except Exception as e:
        print(f"❌ Error during search: {e}")
        return []

    if len(indices[0]) == 0 or indices[0][0] == -1:
        print(f"ℹ️ No results found for query: '{query}'")
        return []

    books = []

    print(f"\n[search_books] Query: '{query}'")
    print("Rank | Book ID | Similarity Score")
    print("-" * 40)

    for i in range(len(indices[0])):
        idx = indices[0][i]
        if idx == -1:
            continue

        book_id = ordered_ids[idx]
        similarity = float(distances[0][i])

        print(f"{i+1:4} | {book_id:12} | {similarity:.4f}")

        # ✅ FIXED LOGIC (use similarity directly)
        if similarity < MIN_SIMILARITY:
            continue

        if min_score is not None and similarity < min_score:
            continue

        books.append({
            "book_id": book_id,
            "score": round(similarity, 4),
        })

    # ✅ fallback (keep this)
    if not books:
        print(f"⚠️ No results passed threshold ({MIN_SIMILARITY}), returning top results")
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx == -1:
                continue

            book_id = ordered_ids[idx]
            similarity = float(distances[0][i])

            books.append({
                "book_id": book_id,
                "score": round(similarity, 4),
            })

    return books


def get_collection_stats():
    """Get statistics about the FAISS collection"""
    try:
        from retrieval.faiss_client import get_collection_stats as faiss_stats
        return faiss_stats()
    except Exception as e:
        return {
            "error": str(e),
            "total_embeddings": 0,
            "has_data": False
        }