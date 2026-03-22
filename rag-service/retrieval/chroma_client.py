# retrieval/chroma_client.py
import os
import chromadb
import tarfile
from pathlib import Path

# Determine base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Production-only configuration
# Use persistent path on Render (can be /tmp or persistent disk)
CHROMA_DIR = os.environ.get('CHROMA_PERSIST_DIR', '/tmp/chroma_store')

print(f"📂 Using Chroma directory: {CHROMA_DIR}")
print(f"🌍 Environment: Production")

# Ensure directory exists
os.makedirs(CHROMA_DIR, exist_ok=True)

# Check if we need to extract packaged chroma data
if not os.listdir(CHROMA_DIR):
    print("📦 Chroma directory is empty, looking for packaged data...")
    
    # Look for chroma_store.tar.gz in the backend root
    tar_path = os.path.join(BASE_DIR, "chroma_store.tar.gz")
    
    if os.path.exists(tar_path):
        print(f"📦 Found packaged chroma data at {tar_path}, extracting...")
        try:
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(path=CHROMA_DIR)
            print(f"✅ Successfully extracted chroma data to {CHROMA_DIR}")
            
            # Verify extraction
            extracted_files = os.listdir(CHROMA_DIR)
            print(f"📁 Extracted {len(extracted_files)} items: {extracted_files[:5]}")  # Show first 5 items
        except Exception as e:
            print(f"❌ Error extracting chroma data: {e}")
            raise
    else:
        print(f"⚠️ No packaged chroma data found at {tar_path}")
        print("⚠️ Starting with empty chroma store")
else:
    print(f"✅ Chroma directory already contains {len(os.listdir(CHROMA_DIR))} items")

# Initialize ChromaDB client
try:
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    print(f"✅ ChromaDB client initialized at {CHROMA_DIR}")
except Exception as e:
    print(f"❌ Error initializing ChromaDB: {e}")
    raise

def get_chroma_collection():
    """Get or create the books collection"""
    try:
        collection = client.get_or_create_collection(name="books")
        
        # Log collection stats
        count = collection.count()
        print(f"📚 Books collection has {count} embeddings")
        
        # If collection is empty but we have files, something is wrong
        if count == 0 and os.listdir(CHROMA_DIR):
            print(f"⚠️ Warning: Chroma directory has files but collection is empty!")
            print(f"📁 Directory contents: {os.listdir(CHROMA_DIR)}")
        
        return collection
    except Exception as e:
        print(f"❌ Error getting chroma collection: {e}")
        raise

# Initialize collection on import
try:
    collection = get_chroma_collection()
    print(f"✅ ChromaDB ready with {collection.count()} book embeddings")
except Exception as e:
    print(f"⚠️ ChromaDB initialization error: {e}")
    collection = None
