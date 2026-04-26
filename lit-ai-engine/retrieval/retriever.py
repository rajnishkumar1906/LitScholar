"""
retriever.py - FAISS + DB retrieval pipeline
"""

from retrieval.faiss_client import search
from retrieval.neon_fetch import fetch_books_by_ids

MIN_SCORE = 0.35


async def retrieve_books(query: str, top_k: int = 10):

    if not query.strip():
        return []

    # 🔍 FAISS search
    results = search(query, top_k=top_k)

    if not results:
        return []

    # filter by score
    filtered = [r for r in results if r["score"] >= MIN_SCORE]

    if not filtered:
        filtered = results  # fallback

    book_ids = [r["book_id"] for r in filtered]

    # 📚 DB fetch
    books = await fetch_books_by_ids(book_ids)

    if not books:
        return []

    # maintain order
    id_map = {b["book_id"]: b for b in books}

    final = []
    for r in filtered:
        bid = r["book_id"]
        if bid in id_map:
            book = id_map[bid]
            book["score"] = r["score"]
            final.append(book)

    return final