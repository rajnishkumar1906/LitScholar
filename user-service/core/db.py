import asyncpg
import asyncio
from core.config import settings

async def get_async_db():
    """
    Asynchronous PostgreSQL connection using asyncpg.
    """
    try:
        # Use a timeout to avoid hanging
        conn = await asyncio.wait_for(
            asyncpg.connect(settings.DB_URL_NEON),
            timeout=10.0
        )
        try:
            yield conn
        finally:
            await conn.close()
    except asyncio.TimeoutError:
        print("DATABASE CONNECTION TIMEOUT: Could not reach Neon DB in 10s")
        raise Exception("Database connection timeout. Check your network or DB URL.")
    except Exception as e:
        print(f"DATABASE CONNECTION FAILED: {str(e)}")
        # Re-raise so FastAPI captures it
        raise