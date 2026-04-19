"""
faiss_client.py - FAISS-based book retrieval
"""

import os
import json
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Determine base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# FAISS store directory (reusing existing structure)
FAISS_DIR = os.path.join(BASE_DIR, "faiss_store")

# For production (Render) - use persistent path
PROD_FAISS_DIR = os.environ.get('FAISS_PERSIST_DIR', '/tmp/faiss_store')

# Decide which directory to use based on environment
IS_PRODUCTION = os.environ.get('ENVIRONMENT') == 'production'
FAISS_STORE_DIR = PROD_FAISS_DIR if IS_PRODUCTION else FAISS_DIR

# FAISS file paths
FAISS_INDEX_PATH = os.path.join(FAISS_STORE_DIR, "books.index")
FAISS_IDS_PATH = os.path.join(FAISS_STORE_DIR, "books_ids.json")
FAISS_META_PATH = os.path.join(FAISS_STORE_DIR, "books_meta.json")

print(f"📂 Using FAISS directory: {FAISS_STORE_DIR}")
print(f"🌍 Environment: {'Production' if IS_PRODUCTION else 'Development'}")

# Global variables
_index = None
_ordered_ids = None
_meta_store = None
_model = None

def ensure_faiss_dir():
    """Ensure FAISS directory exists"""
    os.makedirs(FAISS_STORE_DIR, exist_ok=True)

def load_faiss_index():
    """Load FAISS index and metadata"""
    global _index, _ordered_ids, _meta_store
    
    ensure_faiss_dir()
    
    if not os.path.exists(FAISS_INDEX_PATH):
        print(f"❌ FAISS index not found at {FAISS_INDEX_PATH}")
        print("💡 Please run the embedding pipeline first")
        return False
    
    try:
        # Load FAISS index
        print("⚡ Loading FAISS index...")
        _index = faiss.read_index(FAISS_INDEX_PATH)
        
        # Load ordered IDs
        with open(FAISS_IDS_PATH, 'r', encoding='utf-8') as f:
            _ordered_ids = json.load(f)
        
        # Load metadata
        with open(FAISS_META_PATH, 'r', encoding='utf-8') as f:
            _meta_store = json.load(f)
        
        print(f"✅ FAISS index loaded: {_index.ntotal} vectors")
        print(f"📚 Metadata loaded: {len(_meta_store)} books")
        return True
        
    except Exception as e:
        print(f"❌ Error loading FAISS index: {e}")
        return False

def get_model():
    """Get or load the sentence transformer model"""
    global _model
    
    if _model is None:
        print("🔄 Loading embedding model: all-mpnet-base-v2")
        
        # For production, set device explicitly
        device = os.environ.get('MODEL_DEVICE', 'cpu')
        
        # Load model
        _model = SentenceTransformer(
            "all-mpnet-base-v2",
            device=device,
            cache_folder=os.environ.get('MODEL_CACHE_DIR', "/tmp/model_cache")
        )
        
        # Optional: Use half precision for faster inference
        if os.environ.get('USE_FP16', 'false').lower() == 'true':
            try:
                _model.half()
                print("✅ Using FP16 precision for faster inference")
            except:
                print("⚠️ FP16 not supported, using FP32")
        
        print("✅ Embedding model loaded successfully")
    
    return _model

def get_faiss_collection():
    """Get FAISS collection (compatible with Chroma interface)"""
    if _index is None:
        if not load_faiss_index():
            raise Exception("FAISS index not available")
    
    return {
        "index": _index,
        "ordered_ids": _ordered_ids,
        "meta_store": _meta_store
    }

def get_collection_stats():
    """Get statistics about the FAISS collection"""
    try:
        if _index is None:
            load_faiss_index()
        
        return {
            "total_embeddings": _index.ntotal if _index else 0,
            "collection_name": "faiss_books",
            "has_data": _index.ntotal > 0 if _index else False,
            "backend": "FAISS"
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_embeddings": 0,
            "has_data": False,
            "backend": "FAISS"
        }