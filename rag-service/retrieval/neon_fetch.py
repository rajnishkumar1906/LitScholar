import asyncpg
import asyncio
from typing import List, Dict, Any, Optional
from core.config import settings

# Global connection pool
_pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
    """Get or create connection pool for Neon database"""
    global _pool

    if _pool is None:
        if not settings.DB_URL_NEON:
            print("❌ DB_URL_NEON is not set. Please check your .env file or environment variables.")
            raise ValueError("Missing DB_URL_NEON configuration")

        try:
            print("🔌 Creating Neon DB connection pool...")
            
            # Create connection pool
            _pool = await asyncpg.create_pool(
                settings.DB_URL_NEON,
                min_size=1,
                max_size=5,
                command_timeout=60,
                ssl='require' if settings.DB_URL_NEON and 'neon.tech' in str(settings.DB_URL_NEON) else 'prefer'
            )
            
            # Test connection with timeout
            try:
                async with asyncio.timeout(10):
                    async with _pool.acquire() as conn:
                        await conn.execute("SELECT 1")
                print("✅ Neon DB connection pool created successfully")
            except asyncio.TimeoutError:
                print("❌ Connection test timed out")
                await _pool.close()
                _pool = None
                raise
                
        except Exception as e:
            print(f"❌ Failed to create Neon DB pool: {e}")
            if _pool:
                await _pool.close()
                _pool = None
            raise

    return _pool


async def fetch_books_by_ids(book_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch multiple books by their IDs from Neon database
    
    Args:
        book_ids: List of book IDs to fetch
        
    Returns:
        List of book dictionaries with standardized keys
    """
    if not book_ids:
        return []

    # Clean and validate IDs
    valid_book_ids = [str(b).strip() for b in book_ids if str(b).strip()]

    if not valid_book_ids:
        print("⚠️ No valid book IDs provided")
        return []

    query = """
        SELECT
            book_id,
            book_title,
            author,
            genres,
            book_details,
            num_pages,
            cover_image_url
        FROM books
        WHERE book_id = ANY($1::text[])
    """

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, valid_book_ids)
        
        print(f"📚 Fetched {len(rows)} books from Neon DB")
        
        # If no rows found, try to see if the table exists
        if len(rows) == 0 and len(valid_book_ids) > 0:
            # Check if table exists (debug)
            async with pool.acquire() as conn:
                table_check = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'books'
                    )
                """)
                if not table_check:
                    print("❌ 'books' table does not exist in database")
                else:
                    # Check column names
                    columns = await conn.fetch("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'books'
                    """)
                    col_names = [c['column_name'] for c in columns]
                    print(f"📋 Available columns: {col_names}")

    except asyncpg.PostgresError as e:
        print(f"❌ Neon DB error: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error in fetch_books_by_ids: {e}")
        return []

    books = [
        {
            "book_id": r["book_id"],
            "title": r["book_title"],
            "author": r["author"],
            "genres": r["genres"],
            "description": r["book_details"],
            "num_pages": r["num_pages"],
            "image_url": r["cover_image_url"],
        }
        for r in rows
    ]

    return books


async def close_pool():
    """Close the connection pool (call on app shutdown)"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        print("🔌 Neon DB connection pool closed")