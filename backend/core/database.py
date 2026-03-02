import psycopg
from core.config import settings

def get_db():
    conn = psycopg.connect(settings.DB_URL_NEON)
    try:
        yield conn
    finally:
        conn.close()