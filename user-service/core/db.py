import asyncpg
import asyncio
from core.config import settings

async def get_async_db():
    """Async DB connection dependency."""
    try:
        # Connect with timeout
        conn = await asyncio.wait_for(
            asyncpg.connect(settings.DB_URL_NEON),
            timeout=10.0
        )
        try:
            yield conn
        finally:
            # Always close connection
            await conn.close()

    except asyncio.TimeoutError:
        print("DB TIMEOUT: Could not connect in 10s")
        raise Exception("Database connection timeout")

    except Exception as e:
        print(f"DB ERROR: {str(e)}")
        raise