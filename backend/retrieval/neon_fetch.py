# import asyncpg
# from core.config import settings

# async def fetch_books_by_ids(book_ids: list[str]):
#     if not book_ids:
#         return []

#     # Convert everything to strings explicitly
#     valid_book_ids = []
#     for bid in book_ids:
#         try:
#             # Force convert to string
#             str_bid = str(bid).strip()
#             if str_bid:
#                 valid_book_ids.append(str_bid)
#         except Exception:
#             continue
    
#     if not valid_book_ids:
#         return []

#     # Create placeholders
#     placeholders = ",".join([f"${i+1}" for i in range(len(valid_book_ids))])

#     query = f"""
#         SELECT
#             book_id,
#             book_title,
#             author,
#             genres,
#             book_details,
#             summary,
#             num_pages,
#             cover_image_url
#         FROM books
#         WHERE book_id IN ({placeholders});
#     """

#     conn = await asyncpg.connect(settings.DB_URL_NEON)
#     try:
#         rows = await conn.fetch(query, *valid_book_ids)
#     except Exception as e:
#         print(f"❌ Database error in fetch_books_by_ids: {e}")
#         return []
#     finally:
#         await conn.close()

#     books = [{
#         "book_id": r["book_id"],
#         "title": r["book_title"],
#         "author": r["author"],
#         "genres": r["genres"],
#         "description": r["book_details"],
#         "summary": r["summary"],
#         "num_pages": r["num_pages"],
#         "image_url": r["cover_image_url"],
#     } for r in rows]

#     return books


import asyncpg
from core.config import settings

pool = None


async def get_pool():
    global pool

    if pool is None:
        pool = await asyncpg.create_pool(
            settings.DB_URL_NEON,
            min_size=1,
            max_size=5,
        )

    return pool


async def fetch_books_by_ids(book_ids: list[str]):
    if not book_ids:
        return []

    # Clean IDs
    valid_book_ids = [str(b).strip() for b in book_ids if str(b).strip()]

    if not valid_book_ids:
        return []

    query = """
        SELECT
            book_id,
            book_title,
            author,
            genres,
            book_details,
            summary,
            num_pages,
            cover_image_url
        FROM books
        WHERE book_id = ANY($1)
    """

    try:
        pool = await get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, valid_book_ids)

    except Exception as e:
        print(f"❌ Neon DB error: {e}")
        return []

    books = [
        {
            "book_id": r["book_id"],
            "title": r["book_title"],
            "author": r["author"],
            "genres": r["genres"],
            "description": r["book_details"],
            "summary": r["summary"],
            "num_pages": r["num_pages"],
            "image_url": r["cover_image_url"],
        }
        for r in rows
    ]

    return books