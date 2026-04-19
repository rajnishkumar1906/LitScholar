"""
faiss_searcher.py - FAISS-based book search interface
"""

import os
import json
import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

FAISS_DIR = "faiss_store"
FAISS_INDEX_PATH = os.path.join(FAISS_DIR, "books.index")
FAISS_IDS_PATH = os.path.join(FAISS_DIR, "books_ids.json")
FAISS_META_PATH = os.path.join(FAISS_DIR, "books_meta.json")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "all-mpnet-base-v2"
MAX_LENGTH = 256


class FAISSSearcher:
    """FAISS-based book searcher"""
    
    def __init__(self):
        print("⚡ Loading FAISS index...")
        
        if not os.path.exists(FAISS_INDEX_PATH):
            raise FileNotFoundError(
                f"\n❌ FAISS index not found at {FAISS_INDEX_PATH}\n"
                f"Please run: python build_faiss_embeddings.py first\n"
            )
        
        self.index = faiss.read_index(FAISS_INDEX_PATH)
        print(f"📊 Loaded {self.index.ntotal} book embeddings")
        
        with open(FAISS_IDS_PATH, "r", encoding="utf-8") as f:
            self.ordered_ids = json.load(f)
        
        with open(FAISS_META_PATH, "r", encoding="utf-8") as f:
            self.meta_store = json.load(f)
        
        print("🧠 Loading sentence transformer model...")
        self.model = SentenceTransformer(MODEL_NAME, device=DEVICE)
        print(f"✅ FAISS Searcher ready (device: {DEVICE})\n")
    
    def search(self, query_text: str, k: int = 10) -> list[dict]:
        """
        Search for books similar to query text
        
        Args:
            query_text: Search query string
            k: Number of results to return
            
        Returns:
            List of dictionaries with book metadata and similarity scores
        """
        # Encode query
        with torch.no_grad():
            vec = self.model.encode(
                [query_text],
                normalize_embeddings=True,
                max_length=MAX_LENGTH,
                show_progress_bar=False,
            )
        
        # Search FAISS index
        vec_np = np.array(vec, dtype="float32")
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(vec_np, k)
        
        # Format results
        results = []
        for rank, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:
                continue
            
            book_id = self.ordered_ids[idx]
            metadata = self.meta_store.get(book_id, {})
            
            results.append({
                "rank": rank + 1,
                "similarity_score": round(float(distance), 4),
                **metadata
            })
        
        return results


def interactive_search():
    """Run interactive search session"""
    print("\n" + "=" * 60)
    print("📚 FAISS BOOK SEARCH ENGINE")
    print("=" * 60)
    
    try:
        searcher = FAISSSearcher()
    except FileNotFoundError as e:
        print(e)
        return
    
    print("💡 Example queries:")
    print("   • 'fantasy adventure with magic'")
    print("   • 'romance novels'")
    print("   • 'science fiction artificial intelligence'")
    print("   • 'mystery thriller plot twist'")
    print("   • Type 'quit' to exit\n")
    
    while True:
        print("-" * 60)
        query = input("🔍 Search: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        if not query:
            print("⚠️ Please enter a search query\n")
            continue
        
        print(f"\n📖 Searching: '{query}'\n")
        
        try:
            results = searcher.search(query, k=10)
            
            if not results:
                print("❌ No results found. Try a different query.\n")
                continue
            
            print(f"✅ Found {len(results)} results:\n")
            
            for book in results:
                print(f"[{book['rank']}] {book['book_title']}")
                print(f"    Author: {book['author']}")
                print(f"    Genres: {book['genres']}")
                print(f"    Pages: {book['num_pages']}")
                print(f"    Similarity: {book['similarity_score']:.4f}")
                
                if book.get('book_details'):
                    desc = book['book_details'][:150]
                    if len(book['book_details']) > 150:
                        desc += "..."
                    print(f"    Description: {desc}")
                print()
                
        except Exception as e:
            print(f"❌ Search error: {e}\n")


if __name__ == "__main__":
    interactive_search()