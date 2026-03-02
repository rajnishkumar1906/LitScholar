import psycopg
from core.config import settings

def fetch_books_by_ids(book_ids: list[str]):
    if not book_ids:
        return []

    placeholders = ",".join(["%s"] * len(book_ids))

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

    with psycopg.connect(settings.DB_URL_NEON) as conn:
        with conn.cursor() as cur:
            cur.execute(query, book_ids)
            rows = cur.fetchall()

    books = [{
        "book_id": r[0],
        "title": r[1],
        "author": r[2],
        "genres": r[3],
        "description": r[4],
        "num_pages": r[5],
        "image_url": r[6],
    } for r in rows]

    # preserve ranking
    book_map = {b["book_id"]: b for b in books}
    return [book_map[i] for i in book_ids if i in book_map]