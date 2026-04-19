"""
run_pipeline.py - Complete pipeline for FAISS book search
Single entry point: handles building embeddings, searching, and everything
"""

import os
import csv
import json
import math
import torch
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from datetime import datetime

# ===== CONFIGURATION =====
CSV_PATH = "books_clean.csv"
FAISS_DIR = "faiss_store"
FAISS_INDEX_PATH = os.path.join(FAISS_DIR, "books.index")
FAISS_META_PATH = os.path.join(FAISS_DIR, "books_meta.json")
FAISS_IDS_PATH = os.path.join(FAISS_DIR, "books_ids.json")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 64
EMBEDDING_DIM = 768
MAX_LENGTH = 256
# =========================

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"📚 {title}")
    print("="*60)

def check_csv_exists():
    """Check if CSV file exists"""
    if not os.path.exists(CSV_PATH):
        print(f"\n❌ Error: {CSV_PATH} not found!")
        print(f"Please ensure {CSV_PATH} is in the current directory")
        return False
    return True

def check_embeddings_exist():
    """Check if FAISS embeddings already exist"""
    return all([
        os.path.exists(FAISS_INDEX_PATH),
        os.path.exists(FAISS_IDS_PATH),
        os.path.exists(FAISS_META_PATH)
    ])

def build_embeddings():
    """Build FAISS embeddings from CSV"""
    print_header("BUILDING FAISS EMBEDDINGS")
    print(f"🔥 Device: {DEVICE}")
    if not torch.cuda.is_available():
        print("🐢 Using CPU (this may take a while for large datasets)")
    print()
    
    # Load books
    print(f"📖 Reading {CSV_PATH}...")
    books = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('book_id'):
                books.append(row)
    
    if not books:
        print("❌ No valid books found in CSV!")
        return False
    
    print(f"📦 Loaded {len(books)} books")
    
    # Load model
    print("\n🧠 Loading AI model (first time may download ~1GB)...")
    model = SentenceTransformer("all-mpnet-base-v2", device=DEVICE)
    print("✅ Model loaded")
    
    # Create FAISS directory
    os.makedirs(FAISS_DIR, exist_ok=True)
    
    # Initialize
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    ordered_ids = []
    meta_store = {}
    
    # Process in batches
    total_batches = math.ceil(len(books) / BATCH_SIZE)
    print(f"\n🔄 Processing {len(books)} books in {total_batches} batches...\n")
    
    for batch_num in range(total_batches):
        start = batch_num * BATCH_SIZE
        end = min(start + BATCH_SIZE, len(books))
        batch = books[start:end]
        
        print(f"📊 Batch {batch_num + 1}/{total_batches} (rows {start + 1}-{end})")
        
        # Create texts for embedding
        texts = []
        for book in batch:
            text = (
                f"Title: {book.get('book_title', '')}\n"
                f"Author: {book.get('author', '')}\n"
                f"Genres: {book.get('genres', '')}\n"
                f"Pages: {book.get('num_pages', '')}\n"
                f"Description: {book.get('book_details', '')}"
            )
            texts.append(text)
        
        # Generate embeddings
        with torch.no_grad():
            embeddings = model.encode(
                texts,
                batch_size=BATCH_SIZE,
                normalize_embeddings=True,
                max_length=MAX_LENGTH,
                show_progress_bar=True,
            )
        
        # Add to index
        embeddings_np = np.array(embeddings, dtype="float32")
        index.add(embeddings_np)
        
        # Store metadata
        for book in batch:
            book_id = str(book['book_id'])
            ordered_ids.append(book_id)
            meta_store[book_id] = {
                "book_id": book_id,
                "book_title": book.get('book_title', ''),
                "author": book.get('author', ''),
                "genres": book.get('genres', ''),
                "book_details": book.get('book_details', ''),
                "num_pages": book.get('num_pages', ''),
            }
        
        print(f"✅ Stored {len(batch)} embeddings (Total: {index.ntotal})\n")
        
        if DEVICE == "cuda":
            torch.cuda.empty_cache()
    
    # Save everything
    print("💾 Saving FAISS index...")
    faiss.write_index(index, FAISS_INDEX_PATH)
    
    print("💾 Saving metadata...")
    with open(FAISS_IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(ordered_ids, f)
    
    with open(FAISS_META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta_store, f, ensure_ascii=False)
    
    print_header("EMBEDDING COMPLETE")
    print(f"📊 Total books indexed: {index.ntotal}")
    print(f"📁 FAISS store: {FAISS_DIR}")
    
    return True

def search_books():
    """Interactive book search with quit option"""
    print_header("FAISS BOOK SEARCH ENGINE")
    
    # Load FAISS index
    print("⚡ Loading FAISS index...")
    try:
        index = faiss.read_index(FAISS_INDEX_PATH)
        with open(FAISS_IDS_PATH, "r", encoding="utf-8") as f:
            ordered_ids = json.load(f)
        with open(FAISS_META_PATH, "r", encoding="utf-8") as f:
            meta_store = json.load(f)
        print(f"📊 Loaded {index.ntotal} book embeddings")
    except Exception as e:
        print(f"❌ Failed to load FAISS index: {e}")
        return
    
    # Load model
    print("🧠 Loading AI model...")
    model = SentenceTransformer("all-mpnet-base-v2", device=DEVICE)
    print(f"✅ Ready (device: {DEVICE})\n")
    
    # Search loop
    while True:
        print("-"*60)
        query = input("🔍 Enter your search query (or 'quit' to exit): ").strip()
        
        # Check for quit
        if query.lower() in ['quit', 'exit', 'q', 'bye']:
            print("\n👋 Goodbye! Thanks for using Book Search!")
            break
        
        # Check for empty query
        if not query:
            print("⚠️ Please enter a search query\n")
            continue
        
        print(f"\n📖 Searching for: '{query}'\n")
        
        try:
            # Encode query
            with torch.no_grad():
                vec = model.encode(
                    [query],
                    normalize_embeddings=True,
                    max_length=MAX_LENGTH,
                    show_progress_bar=False,
                )
            
            # Search
            vec_np = np.array(vec, dtype="float32")
            k = min(10, index.ntotal)
            distances, indices = index.search(vec_np, k)
            
            # Display results
            results_found = False
            for rank, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:
                    continue
                
                results_found = True
                book_id = ordered_ids[idx]
                book = meta_store.get(book_id, {})
                similarity = round(float(distance), 4)
                
                print(f"[{rank + 1}] {book.get('book_title', 'Unknown')}")
                print(f"    Author: {book.get('author', 'Unknown')}")
                print(f"    Genres: {book.get('genres', 'N/A')}")
                print(f"    Pages: {book.get('num_pages', 'N/A')}")
                print(f"    Similarity: {similarity:.4f}")
                
                # Show description preview
                desc = book.get('book_details', '')
                if desc:
                    desc_preview = desc[:150] + "..." if len(desc) > 150 else desc
                    print(f"    Description: {desc_preview}")
                print()
            
            if not results_found:
                print("❌ No results found. Try a different query.\n")
                
        except Exception as e:
            print(f"❌ Search error: {e}\n")

def main():
    """Main pipeline - handles everything"""
    print_header("FAISS BOOK SEARCH PIPELINE")
    print("This tool will help you search through your book collection")
    print()
    
    # Check if CSV exists
    if not check_csv_exists():
        return
    
    # Check if embeddings need to be built
    if not check_embeddings_exist():
        print("\n📊 FAISS embeddings not found. Building now...")
        response = input("Do you want to build embeddings? (yes/no): ").strip().lower()
        
        if response in ['yes', 'y']:
            if not build_embeddings():
                print("\n❌ Failed to build embeddings. Please check errors above.")
                return
        else:
            print("\n❌ Cannot search without embeddings. Exiting.")
            return
    else:
        print("\n✅ FAISS embeddings already exist")
        response = input("Do you want to rebuild embeddings? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            if not build_embeddings():
                print("\n❌ Failed to rebuild embeddings.")
                return
    
    # Start search
    print("\n" + "="*60)
    print("🎉 Ready to search! Type 'quit' to exit")
    print("="*60)
    search_books()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")