from sentence_transformers import SentenceTransformer
from retrieval.chroma_client import get_chroma_collection

model = None

MAX_DISTANCE = 0.7


def get_model():
    global model

    if model is None:
        print("Loading embedding model...")
        model = SentenceTransformer(
            "all-mpnet-base-v2",
            device="cpu",
        )

    return model


def search_books(query: str, top_k: int = 6, min_score: float | None = None):

    if not query.strip():
        return []

    try:
        collection = get_chroma_collection()
    except Exception as e:
        print(f"❌ Chroma error: {e}")
        return []

    model = get_model()

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    if not results or not results.get("ids") or not results["ids"][0]:
        print(f"[search_books] No results for '{query}'")
        return []

    books = []

    print(f"[search_books] Query: {query}")
    print("Rank | Book ID | Distance | Score")

    for i in range(len(results["ids"][0])):
        book_id = results["ids"][0][i]
        distance = results["distances"][0][i]

        score = 1.0 - distance

        print(f"{i+1:4} | {book_id:12} | {distance:.4f} | {score:.4f}")

        if distance > MAX_DISTANCE:
            continue

        if min_score and score < min_score:
            continue

        books.append(
            {
                "book_id": book_id,
                "score": round(score, 4),
            }
        )

    # Fallback if everything filtered
    if not books:
        for i in range(len(results["ids"][0])):
            book_id = results["ids"][0][i]
            distance = results["distances"][0][i]

            books.append(
                {
                    "book_id": book_id,
                    "score": round(1.0 - distance, 4),
                }
            )

    return books