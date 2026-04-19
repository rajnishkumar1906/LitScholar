import os
import csv
import math
import json
import torch
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DEBUG = True
CSV_PATH = "books_clean.csv"
FAISS_DIR = "faiss_store"
FAISS_INDEX_PATH = os.path.join(FAISS_DIR, "books.index")
FAISS_META_PATH = os.path.join(FAISS_DIR, "books_meta.json")
FAISS_IDS_PATH = os.path.join(FAISS_DIR, "books_ids.json")
EMBEDDING_DIM = 768
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 128
MAX_LENGTH = 256


def debug(msg: str):
    if DEBUG:
        print(msg, flush=True)


def safe(val):
    return str(val).strip() if val else ""


def build_embedding_text(row):
    """Combine book information into searchable text"""
    return (
        f"Title: {safe(row.get('book_title', ''))}\n"
        f"Author: {safe(row.get('author', ''))}\n"
        f"Genres: {safe(row.get('genres', ''))}\n"
        f"Pages: {safe(row.get('num_pages', ''))}\n"
        f"Description: {safe(row.get('book_details', ''))}"
    )


def load_books_from_csv():
    """Load books from existing clean CSV"""
    debug(f"📥 Loading books from: {CSV_PATH}")
    
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")
    
    books = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('book_id'):
                books.append(row)
    
    debug(f"📦 Loaded {len(books)} books")
    return books


def main():
    print("\n" + "=" * 60)
    print("🚀 BUILDING FAISS EMBEDDINGS")
    print("=" * 60)
    print(f"🔥 Device: {DEVICE}")
    if torch.cuda.is_available():
        print(f"🚀 GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("🐢 Using CPU (this may take a while for large datasets)")
    print("=" * 60 + "\n")

    # Create FAISS directory
    os.makedirs(FAISS_DIR, exist_ok=True)

    # Load model
    debug("🧠 Loading SentenceTransformer model...")
    model = SentenceTransformer("all-mpnet-base-v2", device=DEVICE)
    
    # Load books
    books = load_books_from_csv()
    
    if not books:
        print("❌ No books found in CSV!")
        return
    
    # Initialize FAISS index
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    ordered_ids = []
    meta_store = {}
    
    # Process in batches
    total_batches = math.ceil(len(books) / BATCH_SIZE)
    
    for batch_num in range(total_batches):
        start = batch_num * BATCH_SIZE
        end = min(start + BATCH_SIZE, len(books))
        batch = books[start:end]
        
        print(f"\n📊 Processing batch {batch_num + 1}/{total_batches} (rows {start + 1}-{end})")
        
        # Create texts for embedding
        texts = [build_embedding_text(book) for book in batch]
        
        # Generate embeddings
        with torch.no_grad():
            embeddings = model.encode(
                texts,
                batch_size=BATCH_SIZE,
                normalize_embeddings=True,
                max_length=MAX_LENGTH,
                show_progress_bar=True,
            )
        
        # Add to FAISS index
        embeddings_np = np.array(embeddings, dtype="float32")
        index.add(embeddings_np)
        
        # Store metadata
        for book in batch:
            book_id = str(book['book_id'])
            ordered_ids.append(book_id)
            # Store without cover_image_url
            meta_store[book_id] = {
                "book_id": book_id,
                "book_title": safe(book.get('book_title')),
                "author": safe(book.get('author')),
                "genres": safe(book.get('genres')),
                "book_details": safe(book.get('book_details')),
                "num_pages": safe(book.get('num_pages')),
            }
        
        print(f"✅ Stored {len(batch)} embeddings (Total: {index.ntotal})")
        
        if DEVICE == "cuda":
            torch.cuda.empty_cache()
    
    # Save everything
    print("\n💾 Saving FAISS index...")
    faiss.write_index(index, FAISS_INDEX_PATH)
    
    print("💾 Saving metadata...")
    with open(FAISS_IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(ordered_ids, f)
    
    with open(FAISS_META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta_store, f, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("🎉 FAISS EMBEDDING COMPLETE!")
    print(f"📊 Total books indexed: {index.ntotal}")
    print(f"📁 FAISS store location: {FAISS_DIR}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()