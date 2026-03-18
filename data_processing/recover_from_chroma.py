import os
import csv
import chromadb
from pathlib import Path

# Path to the Chroma store in rag-service
BASE_DIR = Path(__file__).parent.parent
CHROMA_DIR = BASE_DIR / "rag-service" / "chroma_store"
OUTPUT_CSV = BASE_DIR / "data" / "books_recovered.csv"

def recover_data():
    if not CHROMA_DIR.exists():
        print(f"❌ Chroma store not found at {CHROMA_DIR}")
        return

    print(f"📂 Connecting to Chroma at {CHROMA_DIR}...")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    try:
        collection = client.get_collection("books")
        count = collection.count()
        print(f"📊 Found {count} embeddings in collection 'books'")
        
        if count == 0:
            print("⚠️ Collection is empty. Nothing to recover.")
            return

        # Fetch all data from Chroma
        # We fetch in batches if it's large, but let's try a direct get first
        results = collection.get(
            include=["metadatas", "documents"]
        )

        metadatas = results.get("metadatas", [])
        ids = results.get("ids", [])

        if not metadatas:
            print("❌ No metadata found in Chroma. Cannot recover book details.")
            return

        print(f"💾 Recovering {len(metadatas)} books to {OUTPUT_CSV}...")
        
        # Ensure data folder exists
        OUTPUT_CSV.parent.mkdir(exist_ok=True)

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            # We use the columns expected by our cleaning script
            fieldnames = ["book_id", "book_title", "author", "genres", "book_details", "num_pages", "cover_image_url"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for i, meta in enumerate(metadatas):
                # Map Chroma metadata back to CSV columns
                # Chroma metadata keys usually match what we put in: 
                # title, author, genres, num_pages, image_url, description
                writer.writerow({
                    "book_id": ids[i],
                    "book_title": meta.get("title", ""),
                    "author": meta.get("author", ""),
                    "genres": meta.get("genres", ""),
                    "book_details": meta.get("description", ""),
                    "num_pages": meta.get("num_pages", 0),
                    "cover_image_url": meta.get("image_url", "")
                })

        print(f"✅ Recovery complete! File saved as: {OUTPUT_CSV}")
        print(f"💡 You can now rename this to 'books_clean.csv' and run the pipeline.")

    except Exception as e:
        print(f"❌ Error during recovery: {e}")

if __name__ == "__main__":
    recover_data()
