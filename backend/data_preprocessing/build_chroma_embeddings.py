import os
import csv
import math
import time
import torch
import psycopg
import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

DEBUG = True

DB_FETCH_SIZE = 500          # for Supabase only
WARMUP_BATCH_SIZE = 8
MAIN_BATCH_SIZE = 128
MAX_LENGTH = 256

CSV_PATH = "backend/data/books_clean.csv"

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CHROMA_DIR = "backend/chroma_store"

def debug(msg: str):
    if DEBUG:
        print(msg, flush=True)


def print_device_info():
    print("\n" + "=" * 60)
    print("🧠 EMBEDDING DEVICE INFO")
    print("=" * 60)
    print(f"🔥 CUDA available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"🚀 GPU: {torch.cuda.get_device_name(0)}")
        print(
            f"💾 GPU memory: "
            f"{torch.cuda.get_device_properties(0).total_memory // (1024**3)} GB"
        )
    else:
        print("🐢 Using CPU")

    print("=" * 60 + "\n")


def safe(val):
    return str(val).strip() if val else ""


def build_embedding_text(row):
    return (
        f"Title: {safe(row['book_title'])}\n"
        f"Author: {safe(row['author'])}\n"
        f"Genres: {safe(row['genres'])}\n"
        f"Pages: {safe(row['num_pages'])}\n"
        f"Description: {safe(row['book_details'])}"
    )


def load_from_supabase(offset: int):
    """Fetch a chunk from Supabase (safe pagination)"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set")

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    book_id,
                    book_title,
                    author,
                    genres,
                    book_details,
                    num_pages
                FROM books
                ORDER BY book_id
                LIMIT %s OFFSET %s
                """,
                (DB_FETCH_SIZE, offset),
            )
            rows = cur.fetchall()

    results = []
    for r in rows:
        results.append({
            "book_id": str(r[0]),
            "book_title": r[1],
            "author": r[2],
            "genres": r[3],
            "book_details": r[4],
            "num_pages": r[5],
        })

    return results

def load_from_csv():
    """Load entire dataset from local CSV (FAST & RELIABLE)"""
    debug(f"📥 Loading data from CSV: {CSV_PATH}")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    debug(f"📦 Loaded {len(rows)} rows from CSV")
    return rows

def main():
    print_device_info()
    os.makedirs(CHROMA_DIR, exist_ok=True)
    debug(f"📁 Chroma directory: {os.path.abspath(CHROMA_DIR)}")

    # ---- Load model ----
    debug("🧠 Loading SentenceTransformer...")
    model = SentenceTransformer("all-mpnet-base-v2", device=DEVICE)
    debug(f"📍 Model device: {model.device}")

    # ---- Chroma ----
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_or_create_collection(
        name="books",
        metadata={"hnsw:space": "cosine"},
    )

    debug(f"📚 Chroma count before: {collection.count()}")

    # ---------- OPTION 1: SUPABASE ----------
    # offset = 0
    # total_rows = 0
    # while True:
    #     rows = load_from_supabase(offset)
    #     if not rows:
    #         break
    #     embed_rows(rows, model, collection, total_rows)
    #     total_rows += len(rows)
    #     offset += DB_FETCH_SIZE

    # ---------- OPTION 2: LOCAL CSV ----------
    rows = load_from_csv()
    embed_rows(rows, model, collection, 0)

    print("\n🎉 EMBEDDING COMPLETE\n")


def embed_rows(rows, model, collection, already_embedded):
    total_batches = math.ceil(len(rows) / MAIN_BATCH_SIZE)

    for i in range(total_batches):
        start = i * MAIN_BATCH_SIZE
        end = min(start + MAIN_BATCH_SIZE, len(rows))
        batch = rows[start:end]

        batch_size = (
            WARMUP_BATCH_SIZE if already_embedded == 0 and i == 0
            else MAIN_BATCH_SIZE
        )

        debug(
            f"\n🚀 Embedding rows {start + 1} → {end} "
            f"(batch_size={batch_size})"
        )

        texts = [build_embedding_text(r) for r in batch]
        ids = [str(r["book_id"]) for r in batch]

        with torch.no_grad():
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                max_length=MAX_LENGTH,
                show_progress_bar=False,
            )

        collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
        )

        debug(f"💾 Stored {len(batch)} embeddings")
        debug(f"📊 Chroma count now: {collection.count()}")

        if DEVICE == "cuda":
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()