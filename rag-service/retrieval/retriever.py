# retrieval/retriever.py
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
        
        # For production, use CPU (most reliable)
        device = 'cpu'
        
        # Load model with production optimizations
        _model = SentenceTransformer(
            "all-mpnet-base-v2",
            device=device,
            cache_folder="/tmp/model_cache"  # Use /tmp for model cache on Render
        )
        
        print("✅ Embedding model loaded successfully")
    
    return _model

def retrieve_books(query: str, top_k: int = 6, min_score: float | None = None):
    """
    Retrieve books using semantic similarity
    
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
        # Get Chroma collection
        collection = get_chroma_collection()
        if collection is None:
            print("❌ Chroma collection not available")
            return []
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
            include=["distances"]  # Only need distances for scoring
        )
        
    except Exception as e:
        print(f"❌ Error during retrieval: {e}")
        return []

    # Check if we got results
    if not results or not results.get("ids") or not results["ids"][0]:
        print(f"ℹ️ No results found for query: '{query}'")
        return []

    books = []
    print(f"\n[retrieve_books] Query: '{query}'")
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

def get_retriever_stats():
    """Get statistics about the retriever and Chroma collection"""
    try:
        collection = get_chroma_collection()
        if collection is None:
            return {
                "error": "Collection not available", 
                "total_embeddings": 0, 
                "has_data": False
            }
        
        count = collection.count()
        
        # Check if model is loaded
        model_loaded = _model is not None
        
        return {
            "total_embeddings": count,
            "collection_name": "books",
            "has_data": count > 0,
            "model_loaded": model_loaded,
            "max_distance_threshold": MAX_DISTANCE
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_embeddings": 0,
            "has_data": False,
            "model_loaded": False
        }
