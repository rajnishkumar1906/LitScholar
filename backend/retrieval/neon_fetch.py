import asyncpg
from core.config import settings

async def fetch_books_by_ids(book_ids: list[str]):
    if not book_ids:
        return []

    print(f"[DEBUG] fetch_books_by_ids received: {book_ids}")
    print(f"[DEBUG] Type of first element: {type(book_ids[0]) if book_ids else 'N/A'}")

    # Convert everything to strings explicitly
    valid_book_ids = []
    for bid in book_ids:
        try:
            # Force convert to string
            str_bid = str(bid).strip()
            if str_bid:
                valid_book_ids.append(str_bid)
                print(f"[DEBUG] Converted {bid} ({type(bid)}) -> {str_bid}")
        except Exception as e:
            print(f"[DEBUG] Failed to convert {bid}: {e}")
            continue
    
    if not valid_book_ids:
        print("[DEBUG] No valid book IDs after conversion")
        return []

    print(f"[DEBUG] Final valid_book_ids: {valid_book_ids}")
    print(f"[DEBUG] Types: {[type(x) for x in valid_book_ids]}")

    # Create placeholders
    placeholders = ",".join([f"${i+1}" for i in range(len(valid_book_ids))])

    query = f"""
        SELECT
            book_id,
            book_title,
            author,
            genres,
            book_details,
            num_pages,
            cover_image_url
        FROM books
        WHERE book_id IN ({placeholders});
    """

    print(f"[DEBUG] Query: {query}")
    print(f"[DEBUG] Parameters: {valid_book_ids}")

    conn = await asyncpg.connect(settings.DB_URL_NEON)
    try:
        rows = await conn.fetch(query, *valid_book_ids)
        print(f"[DEBUG] Database query returned {len(rows)} rows")
    except Exception as e:
        print(f"[DEBUG] Database error: {e}")
        return []
    finally:
        await conn.close()

    books = [{
        "book_id": r["book_id"],
        "title": r["book_title"],
        "author": r["author"],
        "genres": r["genres"],
        "description": r["book_details"],
        "num_pages": r["num_pages"],
        "image_url": r["cover_image_url"],
    } for r in rows]

    return books