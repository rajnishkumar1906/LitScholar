from sentence_transformers import SentenceTransformer
from retrieval.chroma_client import get_chroma_collection

# Load once (process-level singleton)
model = SentenceTransformer("all-mpnet-base-v2", device="cpu")

# Distance threshold (cosine distance, lower = better)
MAX_DISTANCE = 0.6

def search_books(
    query: str,
    top_k: int = 6,
    min_score: float | None = None,
):
    """
    Semantic search over Chroma.

    Returns a ranked list of:
    {
        book_id: str,
        score: float
    }

    score = 1 - cosine_distance (higher is better)
    """

    if not query.strip():
        return []

    collection = get_chroma_collection()
    print(f'Collection count : {collection.count()}')

    print(f'Query : {query}')
    # Encode query
    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()


    # Query Chroma
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    print(f'Raw Chroma ids : {results.get('ids',[[]])[0]}')
    
    if not results or not results.get("ids") or not results["ids"][0]:
        print(f"[search_books] No results at all for query '{query}'")
        return []

    books = []
    print(f"[search_books] Raw top-{top_k} matches for query: '{query}'")
    print("Rank | Book ID          | Distance | Score")

    for i in range(len(results["ids"][0])):
        book_id = results["ids"][0][i]
        distance = results["distances"][0][i]

        # Convert cosine distance → similarity score
        score = 1.0 - distance
        
        # Print every candidate before filtering
        print(f"{i+1:4} | {book_id:16} | {distance:.4f} | {score:.4f}")

        # Distance-based filtering
        if distance > MAX_DISTANCE:
            print(f"     └─ filtered out (distance > {MAX_DISTANCE})")
            continue

        if min_score is not None and score < min_score:
            print(f"     └─ filtered out (score < {min_score})")
            continue

        books.append({
            "book_id": book_id,
            "score": round(score, 4),
        })
        
    print(f"[search_books] After filtering: {len(books)} books kept")
    if books:
        print(f'Kept books: {[b['book_id'] for b in books]}')    
    else:
        print('No books passed the distance/score filter')
    return books