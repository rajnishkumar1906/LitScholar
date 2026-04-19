import asyncpg
import asyncio
import os

async def create_table():
    db_url = "postgresql://neondb_owner:npg_Zf4yCTkE5FMt@ep-orange-boat-ai9pvzcu-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"
    try:
        conn = await asyncpg.connect(db_url)
        print("Connection successful!")
        
        # Create password_reset_tokens table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token TEXT NOT NULL UNIQUE,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                used BOOLEAN DEFAULT FALSE
            );
        """)
        print("Created password_reset_tokens table")
        
        await conn.close()
    except Exception as e:
        print(f"Failed to create table: {e}")

if __name__ == "__main__":
    asyncio.run(create_table())
