"""
setup_neon_schema.py - Create complete database schema on Neon
Run this from root folder: python setup_neon_schema.py
"""

import os
import sys
import psycopg
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

def print_header(title):
    print("\n" + "="*60)
    print(f"🗄️ {title}")
    print("="*60)

def get_db_connection():
    """Get Neon database connection"""
    db_url = os.getenv("DB_URL_NEON")
    
    if not db_url:
        print("\n❌ DB_URL_NEON not found in .env file!")
        print("\n📝 Please add to your .env file:")
        print("DB_URL_NEON=postgresql://username:password@host/dbname?sslmode=require")
        return None
    
    try:
        # Parse URL to hide password in logs
        parsed = urllib.parse.urlparse(db_url)
        print(f"\n🔌 Connecting to: {parsed.hostname}")
        
        conn = psycopg.connect(db_url)
        print("✅ Connected to Neon database")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def drop_existing_tables(conn):
    """Drop existing tables if they exist"""
    print_header("DROPPING EXISTING TABLES")
    
    confirm = input("\n⚠️ This will DELETE all existing data. Continue? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("❌ Cancelled")
        return False
    
    with conn.cursor() as cur:
        # Drop tables in correct order (due to foreign keys)
        tables = ["summaries", "books"]
        
        for table in tables:
            try:
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"✅ Dropped table: {table}")
            except Exception as e:
                print(f"⚠️ Could not drop {table}: {e}")
        
        conn.commit()
    
    print("\n✅ All existing tables dropped")
    return True

def create_books_table(conn):
    """Create books table with correct data types"""
    print_header("CREATING BOOKS TABLE")
    
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                book_id TEXT PRIMARY KEY,
                book_title TEXT NOT NULL,
                author TEXT,
                genres TEXT,
                book_details TEXT,
                num_pages INTEGER,
                cover_image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on book_title for faster searches
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_books_title 
            ON books(book_title)
        """)
        
        # Create index on author
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_books_author 
            ON books(author)
        """)
        
        conn.commit()
    
    print("✅ Books table created")
    print("   - book_id: TEXT (PRIMARY KEY)")
    print("   - book_title: TEXT NOT NULL")
    print("   - author: TEXT")
    print("   - genres: TEXT")
    print("   - book_details: TEXT")
    print("   - num_pages: INTEGER")
    print("   - cover_image_url: TEXT")
    print("   - created_at: TIMESTAMP")
    print("   - updated_at: TIMESTAMP")
    
    return True

def create_summaries_table(conn):
    """Create summaries table for book summaries"""
    print_header("CREATING SUMMARIES TABLE")
    
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id SERIAL PRIMARY KEY,
                book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
                summary TEXT,
                summary_type TEXT DEFAULT 'short',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(book_id, summary_type)
            )
        """)
        
        # Create index on book_id
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_summaries_book_id 
            ON summaries(book_id)
        """)
        
        conn.commit()
    
    print("✅ Summaries table created")
    print("   - id: SERIAL PRIMARY KEY")
    print("   - book_id: TEXT (FOREIGN KEY to books)")
    print("   - summary: TEXT")
    print("   - summary_type: TEXT")
    print("   - created_at: TIMESTAMP")
    print("   - updated_at: TIMESTAMP")
    
    return True

def create_analytics_table(conn):
    """Create analytics table for search tracking (optional)"""
    print_header("CREATING ANALYTICS TABLE")
    
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS search_analytics (
                id SERIAL PRIMARY KEY,
                query TEXT NOT NULL,
                book_id TEXT,
                score FLOAT,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on searched_at for time-based queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_search_analytics_time 
            ON search_analytics(searched_at DESC)
        """)
        
        conn.commit()
    
    print("✅ Analytics table created (optional)")
    
    return True

def verify_schema(conn):
    """Verify that schema was created correctly"""
    print_header("VERIFYING SCHEMA")
    
    with conn.cursor() as cur:
        # Get all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        print("\n📊 Tables created:")
        for table in tables:
            print(f"   ✅ {table[0]}")
        
        # Get column info for books table
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'books'
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Books table columns:")
        for col in cur.fetchall():
            print(f"   - {col[0]}: {col[1]} (nullable: {col[2]})")
    
    return True

def get_table_counts(conn):
    """Get row counts for each table"""
    print_header("TABLE STATISTICS")
    
    with conn.cursor() as cur:
        tables = ["books", "summaries", "search_analytics"]
        
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"📊 {table}: {count} rows")
            except:
                print(f"📊 {table}: 0 rows (table may not exist)")

def main():
    print_header("NEON DATABASE SCHEMA SETUP")
    print("This will create all necessary tables for LitScholar")
    
    # Get connection
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        # Ask if user wants to drop existing tables
        response = input("\n🔄 Drop existing tables and recreate? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            if not drop_existing_tables(conn):
                return
        
        # Create tables
        if not create_books_table(conn):
            return
        
        if not create_summaries_table(conn):
            return
        
        if not create_analytics_table(conn):
            print("⚠️ Analytics table creation skipped (optional)")
        
        # Verify schema
        verify_schema(conn)
        
        # Show statistics
        get_table_counts(conn)
        
        print_header("SETUP COMPLETE")
        print("✅ Database schema created successfully!")
        print("\n💡 Next steps:")
        print("   1. Run: python FAISS_data_preprocessing/sync_books_to_neon.py")
        print("   2. This will populate your database with book data")
        print("   3. Then rebuild FAISS embeddings")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)
    finally:
        conn.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")