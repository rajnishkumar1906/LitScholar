import os
import chromadb
import tarfile
import shutil
from pathlib import Path

# Determine base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# For local development - use existing chroma_store
LOCAL_CHROMA_DIR = os.path.join(BASE_DIR, "chroma_store")

# For production (Render) - use persistent path
PROD_CHROMA_DIR = os.environ.get('CHROMA_PERSIST_DIR', '/opt/chroma_store')

# Decide which directory to use based on environment
IS_PRODUCTION = os.environ.get('ENVIRONMENT') == 'production'
CHROMA_DIR = PROD_CHROMA_DIR if IS_PRODUCTION else LOCAL_CHROMA_DIR

print(f"📂 Using Chroma directory: {CHROMA_DIR}")
print(f"🌍 Environment: {'Production' if IS_PRODUCTION else 'Development'}")

# Ensure directory exists
os.makedirs(CHROMA_DIR, exist_ok=True)

# For production: Check if we need to extract the packaged chroma data
if IS_PRODUCTION and not os.listdir(CHROMA_DIR):
    print("📦 Production: Chroma directory is empty, looking for packaged data...")
    
    # Look for chroma_store.tar.gz in the backend root
    tar_path = os.path.join(BASE_DIR, "chroma_store.tar.gz")
    
    if os.path.exists(tar_path):
        print(f"📦 Found packaged chroma data at {tar_path}, extracting...")
        try:
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(path=CHROMA_DIR)
            print(f"✅ Successfully extracted chroma data to {CHROMA_DIR}")
        except Exception as e:
            print(f"❌ Error extracting chroma data: {e}")
    else:
        print(f"⚠️ No packaged chroma data found at {tar_path}")
        print("⚠️ Starting with empty chroma store")

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
        
        # Log collection stats (optional)
        count = collection.count()
        print(f"📚 Books collection has {count} embeddings")
        
        return collection
    except Exception as e:
        print(f"❌ Error getting chroma collection: {e}")
        raise

# For debugging - print collection count on import
try:
    collection = get_chroma_collection()
    print(f"✅ ChromaDB ready with {collection.count()} book embeddings")
except:
    print("⚠️ ChromaDB collection not yet populated")