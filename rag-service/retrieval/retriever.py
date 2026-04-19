# from sentence_transformers import SentenceTransformer
# from retrieval.chroma_client import get_chroma_collection
# import os

# # Global model instance
# _model = None

# # Configuration - can be overridden by environment variables
# MAX_DISTANCE = float(os.environ.get('CHROMA_MAX_DISTANCE', '0.7'))

# def get_model():
#     """Get or load the sentence transformer model"""
#     global _model
    
#     if _model is None:
#         print("🔄 Loading embedding model: all-mpnet-base-v2")
        
#         # For production, you might want to set device explicitly
#         device = os.environ.get('MODEL_DEVICE', 'cpu')
        
#         # Load model with optimizations for production
#         _model = SentenceTransformer(
#             "all-mpnet-base-v2",
#             device=device,
#             cache_folder=os.environ.get('MODEL_CACHE_DIR', "/tmp/model_cache")  # Optional cache dir
#         )
        
#         # Optional: Use half precision for faster inference (if supported)
#         if os.environ.get('USE_FP16', 'false').lower() == 'true':
#             try:
#                 _model.half()
#                 print("✅ Using FP16 precision for faster inference")
#             except:
#                 print("⚠️ FP16 not supported, using FP32")
        
#         print("✅ Embedding model loaded successfully")
    
#     return _model

# def search_books(query: str, top_k: int = 6, min_score: float | None = None):
#     """
#     Search for books using semantic similarity
    
#     Args:
#         query: Search query text
#         top_k: Number of results to return
#         min_score: Minimum similarity score (0-1) to include
    
#     Returns:
#         List of dicts with book_id and score
#     """
#     if not query or not query.strip():
#         print("⚠️ Empty query provided")
#         return []

#     # Validate top_k
#     if top_k < 1:
#         top_k = 6
    
#     try:
#         # Get Chroma collection (this will handle data extraction if needed)
#         collection = get_chroma_collection()
#     except Exception as e:
#         print(f"❌ Chroma collection error: {e}")
#         return []

#     try:
#         # Get embedding model
#         model = get_model()
        
#         # Encode query
#         query_embedding = model.encode(
#             query,
#             normalize_embeddings=True,
#         ).tolist()
        
#         # Query ChromaDB
#         results = collection.query(
#             query_embeddings=[query_embedding],
#             n_results=top_k,
#             include=["metadatas", "distances"]  # Explicitly include what we need
#         )
        
#     except Exception as e:
#         print(f"❌ Error during search: {e}")
#         return []

#     # Check if we got results
#     if not results or not results.get("ids") or not results["ids"][0]:
#         print(f"ℹ️ No results found for query: '{query}'")
#         return []

#     books = []
#     print(f"\n[search_books] Query: '{query}'")
#     print("Rank | Book ID | Distance | Score")
#     print("-" * 40)

#     for i in range(len(results["ids"][0])):
#         book_id = results["ids"][0][i]
#         distance = results["distances"][0][i]
        
#         # Calculate similarity score (1 - distance for cosine)
#         score = 1.0 - distance
        
#         print(f"{i+1:4} | {book_id:12} | {distance:.4f} | {score:.4f}")
        
#         # Apply filters
#         if distance > MAX_DISTANCE:
#             continue
            
#         if min_score is not None and score < min_score:
#             continue
        
#         books.append({
#             "book_id": book_id,
#             "score": round(score, 4),
#         })

#     # If no books passed filters, return all with scores (fallback)
#     if not books:
#         print(f"⚠️ No results passed filters (max_distance={MAX_DISTANCE}), returning all with scores")
#         for i in range(len(results["ids"][0])):
#             book_id = results["ids"][0][i]
#             distance = results["distances"][0][i]
#             books.append({
#                 "book_id": book_id,
#                 "score": round(1.0 - distance, 4),
#             })

#     return books

# # Optional: Add a function to get collection stats
# def get_collection_stats():
#     """Get statistics about the Chroma collection"""
#     try:
#         collection = get_chroma_collection()
#         count = collection.count()
        
#         # Get a sample to check metadata
#         sample = None
#         if count > 0:
#             sample = collection.get(limit=1)
        
#         return {
#             "total_embeddings": count,
#             "collection_name": collection.name,
#             "has_data": count > 0
#         }
#     except Exception as e:
#         return {
#             "error": str(e),
#             "total_embeddings": 0,
#             "has_data": False
#         }



"""
retriever.py - Book retrieval using FAISS
"""

from sentence_transformers import SentenceTransformer
from retrieval.faiss_client import get_faiss_collection, get_model, load_faiss_index
import os
import numpy as np

# Global model instance
_model = None

# Configuration - can be overridden by environment variables
MAX_DISTANCE = float(os.environ.get('FAISS_MAX_DISTANCE', '0.7'))

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
            cache_folder=os.environ.get('MODEL_CACHE_DIR', "/tmp/model_cache")
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
    Search for books using FAISS semantic similarity
    
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
        # Load FAISS collection if not already loaded
        faiss_data = get_faiss_collection()
        index = faiss_data["index"]
        ordered_ids = faiss_data["ordered_ids"]
    except Exception as e:
        print(f"❌ FAISS collection error: {e}")
        return []

    try:
        # Get embedding model
        model = get_model()
        
        # Encode query
        query_embedding = model.encode(
            query,
            normalize_embeddings=True,
        )
        
        # Convert to numpy array
        query_embedding_np = np.array([query_embedding], dtype="float32")
        
        # Search FAISS index
        distances, indices = index.search(query_embedding_np, top_k)
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        return []

    # Check if we got results
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
        similarity = float(distances[0][i])  # For IndexFlatIP, this is cosine similarity
        
        print(f"{i+1:4} | {book_id:12} | {similarity:.4f}")
        
        # Apply filters (similarity is already 0-1, higher is better)
        if similarity < (1.0 - MAX_DISTANCE):  # Convert MAX_DISTANCE to similarity threshold
            continue
            
        if min_score is not None and similarity < min_score:
            continue
        
        books.append({
            "book_id": book_id,
            "score": round(similarity, 4),
        })

    # If no books passed filters, return all with scores (fallback)
    if not books:
        print(f"⚠️ No results passed filters (max_distance={MAX_DISTANCE}), returning all with scores")
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

# Optional: Add a function to get collection stats
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