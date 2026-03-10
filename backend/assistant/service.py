from typing import List, Dict

from retrieval.retriever import search_books
from retrieval.neon_fetch import fetch_books_by_ids
from assistant.librarian import librarian_answer


def normalize_books(books: List[Dict]) -> List[Dict]:
    """
    Ensure consistent book structure for the assistant pipeline.
    """

    normalized = []

    for b in books:
        normalized.append({
            "book_id": b.get("book_id"),
            "title": b.get("title"),
            "author": b.get("author"),
            "genres": b.get("genres"),
            "image_url": b.get("image_url"),
            "summary": b.get("summary") or b.get("description")
        })

    return normalized


async def assistant_service(question: str, top_k: int):
    """
    Main AI assistant pipeline

    Flow:
    1. Vector search (Chroma)
    2. Fetch books from Neon DB
    3. Generate LLM answer
    4. Return minimal book data
    """

    print(f"🔎 Assistant query: {question}")

    # ---------- STEP 1: VECTOR SEARCH ----------
    try:
        results = search_books(question, top_k=top_k)
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return {
            "answer": "Something went wrong while searching books.",
            "books": []
        }

    if not results:
        print("⚠️ No vector search results")
        return {
            "answer": "I couldn't find any books matching your query.",
            "books": []
        }

    # ---------- STEP 2: FETCH BOOKS ----------
    book_ids = [r["book_id"] for r in results]

    try:
        books = await fetch_books_by_ids(book_ids)
    except Exception as e:
        print(f"❌ Neon fetch failed: {e}")
        return {
            "answer": "I found books but couldn't load their details.",
            "books": []
        }

    if not books:
        print("⚠️ No books returned from database")
        return {
            "answer": "I couldn't retrieve book details from the database.",
            "books": []
        }

    books = normalize_books(books)

    print(f"📚 Books retrieved: {len(books)}")

    # ---------- STEP 3: GENERATE LLM ANSWER ----------
    try:
        llm_result = librarian_answer(question, books)
        answer = llm_result.get("answer", "")
    except Exception as e:
        print(f"❌ LLM generation failed: {e}")
        answer = "I found some books, but couldn't generate a recommendation right now."

    # ---------- STEP 4: PREPARE RESPONSE ----------
    minimal_books = [
        {
            "book_id": b["book_id"],
            "title": b["title"],
            "author": b["author"],
            "genres": b["genres"],
            "image_url": b["image_url"],
        }
        for b in books
    ]

    return {
        "answer": answer,
        "books": minimal_books
    }