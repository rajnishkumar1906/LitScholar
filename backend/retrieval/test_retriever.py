from retriever import search_books
from backend.retrieval.neon_fetch import fetch_books_by_ids

if __name__ == "__main__":
    queries = [
        "fantasy magic adventure",
        "books for teenagers",
        "long epic novel",
        "friendship and growth",
    ]

    for q in queries:
        print("\n🔍 Query:", q)

        results = search_books(q, top_k=5)
        book_ids = [r["book_id"] for r in results]

        books = fetch_books_by_ids(book_ids)

        for b in books:
            print(
                f"📘 {b['title']} | "
                f"{b['author']} | "
                f"{b['genres']}"
            )