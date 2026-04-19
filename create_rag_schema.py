"""
create_rag_schema_safe.py - Create RAG service tables SAFELY
Preserves all existing tables and data
Run: python create_rag_schema_safe.py
"""

import os
import sys
import psycopg
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

DB_URL = os.getenv("DB_URL_NEON")

def print_header(title):
    print("\n" + "="*60)
    print(f"📚 {title}")
    print("="*60)

def get_db_connection():
    """Get Neon database connection"""
    if not DB_URL:
        print("\n❌ DB_URL_NEON not found in .env file!")
        return None
    
    try:
        parsed = urllib.parse.urlparse(DB_URL)
        print(f"\n🔌 Connecting to: {parsed.hostname}")
        conn = psycopg.connect(DB_URL)
        print("✅ Connected to Neon database")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def table_exists(conn, table_name):
    """Check if a table already exists"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
        """, (table_name,))
        return cur.fetchone()[0]

def column_exists(conn, table_name, column_name):
    """Check if a column already exists"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            )
        """, (table_name, column_name))
        return cur.fetchone()[0]

def add_column_if_not_exists(conn, table_name, column_name, column_type, default=None):
    """Add column only if it doesn't exist"""
    if not column_exists(conn, table_name, column_name):
        with conn.cursor() as cur:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default:
                sql += f" DEFAULT {default}"
            cur.execute(sql)
            conn.commit()
            print(f"   ✅ Added column: {table_name}.{column_name}")
        return True
    else:
        print(f"   ⏭️  Column already exists: {table_name}.{column_name}")
        return False

def create_rag_tables_safe(conn):
    """Create ONLY missing RAG service tables (preserves existing)"""
    
    with conn.cursor() as cur:
        
        # ===== BOOK SUMMARY TABLE =====
        print_header("CHECKING BOOK SUMMARY TABLE")
        if not table_exists(conn, "book_summary"):
            cur.execute("""
                CREATE TABLE book_summary (
                    id SERIAL PRIMARY KEY,
                    book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
                    summary TEXT,
                    summary_type VARCHAR(20) DEFAULT 'short',
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(book_id, summary_type)
                )
            """)
            conn.commit()
            print("✅ book_summary table created")
        else:
            print("⏭️  book_summary table already exists - checking for missing columns")
            # Add missing columns if any
            add_column_if_not_exists(conn, "book_summary", "summary_type", "VARCHAR(20)", "'short'")
            add_column_if_not_exists(conn, "book_summary", "generated_at", "TIMESTAMP", "CURRENT_TIMESTAMP")
            add_column_if_not_exists(conn, "book_summary", "updated_at", "TIMESTAMP", "CURRENT_TIMESTAMP")
        
        # ===== USER BOOK VIEWS TABLE =====
        print_header("CHECKING USER BOOK VIEWS TABLE")
        if not table_exists(conn, "user_book_views"):
            cur.execute("""
                CREATE TABLE user_book_views (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
                    click_count INTEGER DEFAULT 1,
                    last_viewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, book_id)
                )
            """)
            conn.commit()
            print("✅ user_book_views table created")
        else:
            print("⏭️  user_book_views table already exists - checking for missing columns")
            add_column_if_not_exists(conn, "user_book_views", "click_count", "INTEGER", "1")
            add_column_if_not_exists(conn, "user_book_views", "last_viewed", "TIMESTAMP", "CURRENT_TIMESTAMP")
            add_column_if_not_exists(conn, "user_book_views", "updated_at", "TIMESTAMP", "CURRENT_TIMESTAMP")
        
        # ===== ASSISTANT CHATS TABLE =====
        print_header("CHECKING ASSISTANT CHATS TABLE")
        if not table_exists(conn, "assistant_chats"):
            cur.execute("""
                CREATE TABLE assistant_chats (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    context_book_ids TEXT[] DEFAULT '{}',
                    citations JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("✅ assistant_chats table created")
        else:
            print("⏭️  assistant_chats table already exists - checking for missing columns")
            add_column_if_not_exists(conn, "assistant_chats", "context_book_ids", "TEXT[]", "'{}'")
            add_column_if_not_exists(conn, "assistant_chats", "citations", "JSONB", "'{}'::jsonb")
        
        # ===== QUIZ SCORES TABLE =====
        print_header("CHECKING QUIZ SCORES TABLE")
        if not table_exists(conn, "quiz_scores"):
            cur.execute("""
                CREATE TABLE quiz_scores (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    book_id TEXT NOT NULL,
                    book_title TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    total_questions INTEGER DEFAULT 5,
                    percentage FLOAT GENERATED ALWAYS AS ((score::float / total_questions::float) * 100) STORED,
                    quiz_results JSONB DEFAULT '[]'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("✅ quiz_scores table created")
        else:
            print("⏭️  quiz_scores table already exists - checking for missing columns")
            add_column_if_not_exists(conn, "quiz_scores", "total_questions", "INTEGER", "5")
            add_column_if_not_exists(conn, "quiz_scores", "percentage", "FLOAT", None)
            add_column_if_not_exists(conn, "quiz_scores", "quiz_results", "JSONB", "'[]'::jsonb")
        
        # ===== USER ACTIVITY TABLE =====
        print_header("CHECKING USER ACTIVITY TABLE")
        if not table_exists(conn, "user_activity"):
            cur.execute("""
                CREATE TABLE user_activity (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    activity_type VARCHAR(50) NOT NULL,
                    book_id TEXT REFERENCES books(book_id) ON DELETE SET NULL,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("✅ user_activity table created")
        else:
            print("⏭️  user_activity table already exists - checking for missing columns")
            add_column_if_not_exists(conn, "user_activity", "metadata", "JSONB", "'{}'::jsonb")
        
        # ===== USER READING PROFILE TABLE =====
        print_header("CHECKING USER READING PROFILE TABLE")
        if not table_exists(conn, "user_reading_profile"):
            cur.execute("""
                CREATE TABLE user_reading_profile (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
                    total_books_read INTEGER DEFAULT 0,
                    total_pages_read INTEGER DEFAULT 0,
                    current_streak INTEGER DEFAULT 0,
                    longest_streak INTEGER DEFAULT 0,
                    last_read_date DATE,
                    yearly_goal INTEGER DEFAULT 0,
                    monthly_goal INTEGER DEFAULT 0,
                    yearly_progress INTEGER DEFAULT 0,
                    monthly_progress INTEGER DEFAULT 0,
                    categories_read JSONB DEFAULT '[]'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("✅ user_reading_profile table created")
        else:
            print("⏭️  user_reading_profile table already exists - checking for missing columns")
            add_column_if_not_exists(conn, "user_reading_profile", "yearly_progress", "INTEGER", "0")
            add_column_if_not_exists(conn, "user_reading_profile", "monthly_progress", "INTEGER", "0")
            add_column_if_not_exists(conn, "user_reading_profile", "categories_read", "JSONB", "'[]'::jsonb")
            add_column_if_not_exists(conn, "user_reading_profile", "updated_at", "TIMESTAMP", "CURRENT_TIMESTAMP")
    
    return True

def create_indexes_safe(conn):
    """Create indexes only if they don't exist"""
    print_header("CREATING MISSING INDEXES")
    
    with conn.cursor() as cur:
        # Define indexes as (name, table, column)
        indexes = [
            ("idx_book_summary_book_id", "book_summary", "book_id"),
            ("idx_user_book_views_user_id", "user_book_views", "user_id"),
            ("idx_user_book_views_book_id", "user_book_views", "book_id"),
            ("idx_user_book_views_last_viewed", "user_book_views", "last_viewed DESC"),
            ("idx_assistant_chats_user_id", "assistant_chats", "user_id"),
            ("idx_assistant_chats_created_at", "assistant_chats", "created_at DESC"),
            ("idx_user_activity_user_id", "user_activity", "user_id"),
            ("idx_user_activity_created_at", "user_activity", "created_at DESC"),
            ("idx_user_activity_type", "user_activity", "activity_type"),
            ("idx_quiz_scores_user_id", "quiz_scores", "user_id"),
            ("idx_quiz_scores_book_id", "quiz_scores", "book_id"),
            ("idx_quiz_scores_created_at", "quiz_scores", "created_at DESC"),
            ("idx_user_reading_profile_user_id", "user_reading_profile", "user_id"),
        ]
        
        for idx_name, table, column in indexes:
            try:
                # Check if index exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM pg_indexes 
                        WHERE indexname = %s
                    )
                """, (idx_name,))
                
                if not cur.fetchone()[0]:
                    cur.execute(f"CREATE INDEX {idx_name} ON {table} ({column})")
                    print(f"✅ Created index: {idx_name}")
                else:
                    print(f"⏭️  Index already exists: {idx_name}")
            except Exception as e:
                print(f"⚠️ Could not create index {idx_name}: {e}")
        
        conn.commit()
    
    return True

def create_triggers_safe(conn):
    """Create triggers only if they don't exist"""
    print_header("CREATING MISSING TRIGGERS")
    
    with conn.cursor() as cur:
        # Create updated_at function if not exists
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)
        print("✅ update_updated_at_column function ready")
        
        # Triggers for tables that have updated_at
        triggers = [
            ("update_book_summary_updated_at", "book_summary"),
            ("update_user_book_views_updated_at", "user_book_views"),
            ("update_user_reading_profile_updated_at", "user_reading_profile"),
        ]
        
        for trigger_name, table in triggers:
            try:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM pg_trigger 
                        WHERE tgname = %s
                    )
                """, (trigger_name,))
                
                if not cur.fetchone()[0] and table_exists(conn, table):
                    cur.execute(f"""
                        CREATE TRIGGER {trigger_name}
                            BEFORE UPDATE ON {table}
                            FOR EACH ROW
                            EXECUTE FUNCTION update_updated_at_column()
                    """)
                    print(f"✅ Created trigger: {trigger_name}")
                else:
                    print(f"⏭️  Trigger already exists: {trigger_name}")
            except Exception as e:
                print(f"⚠️ Could not create trigger {trigger_name}: {e}")
        
        conn.commit()
    
    return True

def verify_schema(conn):
    """Verify all tables exist"""
    print_header("VERIFYING SCHEMA")
    
    with conn.cursor() as cur:
        expected_tables = [
            'book_summary', 'user_book_views', 'assistant_chats',
            'user_activity', 'quiz_scores', 'user_reading_profile'
        ]
        
        print("\n📊 RAG tables status:")
        for table in expected_tables:
            exists = table_exists(conn, table)
            status = "✅" if exists else "❌"
            print(f"   {status} {table}")
        
        # Get row counts for existing tables
        print("\n📈 Current data:")
        for table in expected_tables:
            if table_exists(conn, table):
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"   📊 {table}: {count} rows")

def main():
    print_header("LITSCHOLAR RAG SERVICE - SAFE SCHEMA UPDATE")
    print("⚠️ This script will NOT delete any existing tables or data")
    print("⚠️ It will ONLY add missing tables and columns")
    
    # Get connection
    conn = get_db_connection()
    if not conn:
        sys.exit(1)
    
    try:
        # Check if books table exists (dependency)
        if not table_exists(conn, "books"):
            print("\n❌ Required 'books' table not found!")
            print("Please run create_neon_schema.py first")
            return
        
        # Check if users table exists (dependency)
        if not table_exists(conn, "users"):
            print("\n❌ Required 'users' table not found!")
            print("Please run create_neon_schema.py first")
            return
        
        print("\n📋 Safe operations:")
        print("   ✅ Creating missing tables")
        print("   ✅ Adding missing columns")
        print("   ✅ Creating missing indexes")
        print("   ✅ Creating missing triggers")
        print("   ❌ NOT deleting any data")
        
        response = input("\n✅ Proceed with safe schema update? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Cancelled")
            return
        
        # Create missing tables
        if not create_rag_tables_safe(conn):
            print("❌ Failed to create tables")
            return
        
        # Create missing indexes
        if not create_indexes_safe(conn):
            print("❌ Failed to create indexes")
            return
        
        # Create missing triggers
        if not create_triggers_safe(conn):
            print("❌ Failed to create triggers")
            return
        
        # Verify schema
        verify_schema(conn)
        
        print_header("SAFE SCHEMA UPDATE COMPLETE")
        print("✅ All missing RAG tables and indexes added!")
        print("✅ Existing data preserved!")
        print("\n💡 Next steps:")
        print("   1. Ensure FAISS store is in place: rag-service/faiss_store/")
        print("   2. Start the RAG service: cd rag-service && uvicorn main:app --port 8001")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
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