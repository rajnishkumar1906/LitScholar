import csv
import os
import psycopg # type: ignore
from dotenv import load_dotenv

load_dotenv()

DB_URL_NEON = os.getenv("DB_URL_NEON")
CLEAN_CSV = "data/books_clean.csv"
BATCH_SIZE = 1000


def main():
    if not DB_URL_NEON:
        raise ValueError("DB_URL_NEON not set")

    print(f"📥 Loading clean CSV: {CLEAN_CSV}")

    rows = []
    skipped = 0

    with open(CLEAN_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                book_id = int(r["book_id"])
            except (ValueError, TypeError):
                skipped += 1
                continue

            rows.append((
                book_id,
                r.get("book_title", ""),
                r.get("author", ""),
                r.get("genres", ""),
                r.get("book_details", ""),
                r.get("num_pages", 0),
                r.get("cover_image_url", ""),
            ))

    total = len(rows)
    print(f"📦 Valid rows to insert: {total}")
    if skipped:
        print(f"🚫 Skipped invalid rows: {skipped}")

    query = """
        INSERT INTO books
        (book_id, book_title, author, genres, book_details, num_pages, cover_image_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (book_id) DO NOTHING
    """

    inserted = 0

    with psycopg.connect(DB_URL_NEON) as conn:
        with conn.cursor() as cur:
            for start in range(0, total, BATCH_SIZE):
                batch = rows[start:start + BATCH_SIZE]

                cur.executemany(query, batch)
                inserted += len(batch)

                print(f"🔄 Processed {min(inserted, total)} / {total}")

        conn.commit()

    print("✅ Neon database insert step completed safely")


if __name__ == "__main__":
    main()