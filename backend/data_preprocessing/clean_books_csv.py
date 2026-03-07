import csv
import os

INPUT_CSV = "data/book_raw.csv"
OUTPUT_CSV = "data/books_clean.csv"

OUTPUT_COLUMNS = [
    "book_id",
    "book_title",
    "author",
    "genres",
    "book_details",
    "num_pages",
    "cover_image_url",
]


def clean_text(val):
    return str(val).strip() if val else ""


def clean_num_pages(val):
    if not val:
        return 0
    digits = "".join(c for c in str(val) if c.isdigit())
    return int(digits) if digits else 0


def main():
    # Always rebuild clean CSV to guarantee correctness
    if os.path.exists(OUTPUT_CSV):
        os.remove(OUTPUT_CSV)
        print("🧹 Existing clean CSV removed — rebuilding")

    seen_ids = set()
    cleaned_rows = []
    duplicate_count = 0
    invalid_id_count = 0

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            book_id = clean_text(row.get("book_id"))

            # ---- Validate ID ----
            if not book_id:
                invalid_id_count += 1
                continue

            if book_id in seen_ids:
                duplicate_count += 1
                continue

            seen_ids.add(book_id)

            cleaned_rows.append({
                "book_id": book_id,
                "book_title": clean_text(row.get("book_title")),
                "author": clean_text(row.get("author")),
                "genres": clean_text(row.get("genres")),
                "book_details": clean_text(row.get("book_details")),
                "num_pages": clean_num_pages(row.get("num_pages")),
                "cover_image_url": clean_text(row.get("cover_image_uri")),
            })

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    print("✅ Cleaned CSV written successfully")
    print(f"📦 Unique books written: {len(cleaned_rows)}")
    print(f"🗑️ Duplicate book_id rows removed: {duplicate_count}")
    print(f"🚫 Rows skipped (missing/invalid book_id): {invalid_id_count}")


if __name__ == "__main__":
    main()