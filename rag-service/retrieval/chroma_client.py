# retrieval/chroma_client.py
import os
import shutil
import chromadb
from pathlib import Path

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGED_CHROMA = os.path.join(BASE_DIR, "chroma_store")          # in repo
CHROMA_DIR = os.environ.get('CHROMA_PERSIST_DIR', '/tmp/chroma_store')  # runtime

print(f"📂 Runtime Chroma directory: {CHROMA_DIR}")
print(f"📦 Packaged Chroma source:   {PACKAGED_CHROMA}")

# Ensure runtime directory exists
os.makedirs(CHROMA_DIR, exist_ok=True)

# Copy packaged data if runtime dir is empty
if not os.listdir(CHROMA_DIR):
    if os.path.exists(PACKAGED_CHROMA) and os.listdir(PACKAGED_CHROMA):
        print("📦 Copying packaged chroma data to runtime directory...")
        try:
            shutil.copytree(PACKAGED_CHROMA, CHROMA_DIR, dirs_exist_ok=True)
            print(f"✅ Chroma data copied. Contents: {os.listdir(CHROMA_DIR)}")
        except Exception as e:
            print(f"❌ Failed to copy chroma data: {e}")
            raise
    else:
        print("⚠️ No packaged chroma data found — starting with empty store")
else:
    print(f"✅ Chroma runtime dir already has {len(os.listdir(CHROMA_DIR))} items")

# Initialize ChromaDB client
try:
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    print(f"✅ ChromaDB client initialized at {CHROMA_DIR}")
except Exception as e:
    print(f"❌ ChromaDB init failed: {e}")
    raise

def get_chroma_collection():
    """Get or create the books collection"""
    try:
        collection = client.get_or_create_collection(name="books")
        count = collection.count()
        print(f"📚 Books collection has {count} embeddings")

        if count == 0:
            print("⚠️ Collection is empty — semantic search will return no results")

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
