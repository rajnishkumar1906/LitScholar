"""
pipeline_checks.py - Check status of FAISS pipeline components
"""

import os
import json

CSV_PATH = "books_clean.csv"
FAISS_DIR = "faiss_store"
FAISS_INDEX_PATH = os.path.join(FAISS_DIR, "books.index")
FAISS_IDS_PATH = os.path.join(FAISS_DIR, "books_ids.json")
FAISS_META_PATH = os.path.join(FAISS_DIR, "books_meta.json")


def cleaned_csv_ready() -> bool:
    """Check if clean CSV exists and has data"""
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV file not found: {CSV_PATH}")
        return False
    
    file_size = os.path.getsize(CSV_PATH)
    if file_size == 0:
        print(f"❌ CSV file is empty: {CSV_PATH}")
        return False
    
    print(f"✅ CSV file found: {CSV_PATH} ({file_size} bytes)")
    return True


def faiss_has_embeddings() -> bool:
    """Check if FAISS embeddings exist and are valid"""
    missing_files = []
    
    if not os.path.exists(FAISS_INDEX_PATH):
        missing_files.append("books.index")
    
    if not os.path.exists(FAISS_IDS_PATH):
        missing_files.append("books_ids.json")
    
    if not os.path.exists(FAISS_META_PATH):
        missing_files.append("books_meta.json")
    
    if missing_files:
        print(f"❌ Missing FAISS files: {', '.join(missing_files)}")
        return False
    
    # Verify IDs file is not empty
    try:
        with open(FAISS_IDS_PATH, "r", encoding="utf-8") as f:
            ids = json.load(f)
        
        if not ids:
            print("❌ FAISS IDs file is empty")
            return False
        
        print(f"✅ FAISS embeddings found: {len(ids)} books indexed")
        return True
        
    except Exception as e:
        print(f"❌ Error reading FAISS files: {e}")
        return False


def get_pipeline_status() -> dict:
    """Get complete pipeline status"""
    csv_ready = cleaned_csv_ready()
    faiss_ready = faiss_has_embeddings() if csv_ready else False
    
    return {
        "csv_available": csv_ready,
        "faiss_available": faiss_ready,
        "csv_path": CSV_PATH if csv_ready else None,
        "faiss_path": FAISS_DIR if faiss_ready else None,
    }


def print_status():
    """Print formatted pipeline status"""
    print("\n" + "=" * 60)
    print("📊 FAISS PIPELINE STATUS")
    print("=" * 60)
    
    status = get_pipeline_status()
    
    print(f"\n📁 Data Source:")
    print(f"   • CSV file: {'✅' if status['csv_available'] else '❌'} {CSV_PATH}")
    
    print(f"\n🔍 FAISS Store:")
    print(f"   • Embeddings: {'✅' if status['faiss_available'] else '❌'} {FAISS_DIR}")
    
    if status['csv_available'] and not status['faiss_available']:
        print(f"\n💡 Tip: Run 'python build_faiss_embeddings.py' to build embeddings")
    elif status['faiss_available']:
        print(f"\n💡 Tip: Run 'python faiss_searcher.py' to search books")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    print_status()