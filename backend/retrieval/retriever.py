from sentence_transformers import SentenceTransformer
from retrieval.chroma_client import get_chroma_collection
import os

# Global model instance
_model = None

# Configuration - can be overridden by environment variables
MAX_DISTANCE = float(os.environ.get('CHROMA_MAX_DISTANCE', '0.7'))

def get_model():
    """Get or load the sentence transformer model"""
    global _model
    
    if _model is None:
        print("🔄 Loading embedding model: all-mpnet-base-v2")
        
        # For production, you might want to set device explicitly
        device = os.environ.get('MODEL_DEVICE', 'cpu')
        
        # Load model with optimizations for production
        _model = SentenceTransformer(
            "all-mpnet-base-v2",
            device=device,
            cache_folder=os.environ.get('MODEL_CACHE_DIR', None)  # Optional cache dir
        )
        
        # Optional: Use half precision for faster inference (if supported)
        if os.environ.get('USE_FP16', 'false').lower() == 'true':
            try:
                _model.half()
                print("✅ Using FP16 precision for faster inference")
            except:
                print("⚠️ FP16 not supported, using FP32")
        
        print("✅ Embedding model loaded successfully")
    
    return _model

def search_books(query: str, top_k: int = 6, min_score: float | None = None):
    """
    Search for books using semantic similarity
    
    Args:
        query: Search query text
        top_k: Number of results to return
        min_score: Minimum similarity score (0-1) to include
    
    Returns:
        List of dicts with book_id and score
    """
    if not query or not query.strip():
        print("⚠️ Empty query provided")
        return []

    # Validate top_k
    if top_k < 1:
        top_k = 6
    
    try:
        # Get Chroma collection (this will handle data extraction if needed)
        collection = get_chroma_collection()
    except Exception as e:
        print(f"❌ Chroma collection error: {e}")
        return []

    try:
        # Get embedding model
        model = get_model()
        
        # Encode query
        query_embedding = model.encode(
            query,
            normalize_embeddings=True,
        ).tolist()
        
        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "distances"]  # Explicitly include what we need
        )
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        return []

    # Check if we got results
    if not results or not results.get("ids") or not results["ids"][0]:
        print(f"ℹ️ No results found for query: '{query}'")
        return []

    books = []
    print(f"\n[search_books] Query: '{query}'")
    print("Rank | Book ID | Distance | Score")
    print("-" * 40)

    for i in range(len(results["ids"][0])):
        book_id = results["ids"][0][i]
        distance = results["distances"][0][i]
        
        # Calculate similarity score (1 - distance for cosine)
        score = 1.0 - distance
        
        print(f"{i+1:4} | {book_id:12} | {distance:.4f} | {score:.4f}")
        
        # Apply filters
        if distance > MAX_DISTANCE:
            continue
            
        if min_score is not None and score < min_score:
            continue
        
        books.append({
            "book_id": book_id,
            "score": round(score, 4),
        })

    # If no books passed filters, return all with scores (fallback)
    if not books:
        print(f"⚠️ No results passed filters (max_distance={MAX_DISTANCE}), returning all with scores")
        for i in range(len(results["ids"][0])):
            book_id = results["ids"][0][i]
            distance = results["distances"][0][i]
            books.append({
                "book_id": book_id,
                "score": round(1.0 - distance, 4),
            })

    return books

# Optional: Add a function to get collection stats
def get_collection_stats():
    """Get statistics about the Chroma collection"""
    try:
        collection = get_chroma_collection()
        count = collection.count()
        
        # Get a sample to check metadata
        sample = None
        if count > 0:
            sample = collection.get(limit=1)
        
        return {
            "total_embeddings": count,
            "collection_name": collection.name,
            "has_data": count > 0
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_embeddings": 0,
            "has_data": False
        }