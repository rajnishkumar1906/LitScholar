import asyncpg
from core.config import settings

async def get_async_db():
    """
    Asynchronous PostgreSQL connection using asyncpg.

    Used by async services that rely on asyncpg APIs
    like fetchrow / fetch / execute.
    """
    conn = await asyncpg.connect(settings.DB_URL_NEON)
    try:
        yield conn
    finally:
        await conn.close()