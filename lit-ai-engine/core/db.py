import asyncpg
from core.config import settings


async def get_async_db():
    """
    Async DB connection (asyncpg).
    Used in FastAPI dependencies.
    """
    conn = await asyncpg.connect(settings.DB_URL_NEON)

    try:
        yield conn
    finally:
        await conn.close()