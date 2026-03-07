import os
import psycopg  # type: ignore
import chromadb
from dotenv import load_dotenv
from chromadb.config import Settings

load_dotenv()

DB_URL_NEON = os.getenv("DB_URL_NEON")

CLEAN_CSV_PATH = "data/books_clean.csv"
CHROMA_DIR = "chroma_store"


# ---------- CSV CHECK ----------
def cleaned_csv_ready() -> bool:
    return os.path.exists(CLEAN_CSV_PATH) and os.path.getsize(CLEAN_CSV_PATH) > 0


# ---------- NEON DB CHECK ----------
def neondb_has_books() -> bool:
    if not DB_URL_NEON:
        return False

    with psycopg.connect(DB_URL_NEON) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM books;")
            count = cur.fetchone()[0]

    return count > 0


# ---------- SUMMARY CHECK ----------
def summaries_exist() -> bool:
    """
    Return True only if ALL books already have summaries.
    """

    if not DB_URL_NEON:
        return False

    try:
        with psycopg.connect(DB_URL_NEON) as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM books
                    WHERE summary IS NULL
                    """
                )

                missing = cur.fetchone()[0]

                print(f"📝 Books missing summaries: {missing}")

                # If no missing summaries, we skip
                return missing == 0

    except Exception as e:
        print(f"⚠️ Summary check error: {e}")
        return False


# ---------- CHROMA CHECK (OLD VERSION - COMMENTED) ----------
# def chroma_has_embeddings(collection_name: str = "books") -> bool:
#     if not os.path.exists(CHROMA_DIR):
#         return False
#
#     client = chromadb.Client(
#         Settings(persist_directory=CHROMA_DIR)
#     )
#
#     try:
#         collection = client.get_collection(collection_name)
#         return collection.count() > 0
#     except Exception:
#         return False


# ---------- CHROMA CHECK (CURRENT VERSION) ----------
def chroma_has_embeddings(collection_name: str = "books") -> bool:

    if not os.path.exists(CHROMA_DIR):
        return False

    try:
        # Use SAME persistent directory used during embedding creation
        client = chromadb.PersistentClient(path=CHROMA_DIR)

        collection = client.get_collection(collection_name)

        count = collection.count()

        print(f"📊 Found {count} embeddings in Chroma")

        return count > 0

    except Exception as e:
        print(f"⚠️ Chroma check error: {e}")
        return False