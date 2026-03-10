import os
import chromadb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_store")

print("📂 Using Chroma directory:", CHROMA_DIR)

client = chromadb.PersistentClient(path=CHROMA_DIR)

def get_chroma_collection():
    return client.get_or_create_collection(name="books")