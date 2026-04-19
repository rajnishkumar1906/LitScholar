"""
create_neon_schema.py - Create complete database schema for LitScholar
Run: python create_neon_schema.py
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
    print(f"🗄️ {title}")
    print("="*60)

def get_db_connection():
    """Get Neon database connection"""
    if not DB_URL:
        print("\n❌ DB_URL_NEON not found in .env file!")
        print("\n📝 Please add to your .env file:")
        print("DB_URL_NEON=postgresql://username:password@host/dbname?sslmode=require")
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

def create_schema(conn):
    """Create all tables for LitScholar"""
    
    with conn.cursor() as cur:
        
        # ===== USERS TABLE =====
        print_header("CREATING USERS TABLE")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name VARCHAR(255),
                bio TEXT,
                location VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ users table created")
        
        # ===== BOOKS TABLE =====
        print_header("CREATING BOOKS TABLE")
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
        print("✅ books table created")
        
        # ===== USER READING PROFILE TABLE =====
        print_header("CREATING USER READING PROFILE TABLE")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_reading_profile (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )
        """)
        print("✅ user_reading_profile table created")
        
        # ===== USER BOOKS TABLE =====
        print_header("CREATING USER BOOKS TABLE")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_books (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
                list_type VARCHAR(50) NOT NULL CHECK (list_type IN ('finished', 'reading', 'wishlist')),
                start_date DATE,
                finish_date DATE,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, book_id, list_type)
            )
        """)
        print("✅ user_books table created")
        
        # ===== USER ACTIVITY TABLE =====
        print_header("CREATING USER ACTIVITY TABLE")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                activity_type VARCHAR(50) NOT NULL,
                book_id TEXT REFERENCES books(book_id) ON DELETE SET NULL,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ user_activity table created")
        
        # ===== QUIZ SCORES TABLE =====
        print_header("CREATING QUIZ SCORES TABLE")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_scores (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                book_id TEXT NOT NULL,
                book_title TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER DEFAULT 5,
                quiz_results JSONB DEFAULT '[]'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ quiz_scores table created")
        
        # ===== REFRESH TOKENS TABLE =====
        print_header("CREATING REFRESH TOKENS TABLE")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id SERIAL PRIMARY KEY,
                token TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ refresh_tokens table created")
        
        # ===== PASSWORD RESET TOKENS TABLE =====
        print_header("CREATING PASSWORD RESET TOKENS TABLE")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                otp VARCHAR(6) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ password_reset_tokens table created")
        
        # ===== SUBSCRIPTIONS TABLE (Premium) =====
        print_header("CREATING SUBSCRIPTIONS TABLE")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                plan_name VARCHAR(50) DEFAULT 'premium',
                is_active BOOLEAN DEFAULT TRUE,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ subscriptions table created")
        
        conn.commit()
        
    return True

def create_indexes(conn):
    """Create indexes for better performance"""
    print_header("CREATING INDEXES")
    
    with conn.cursor() as cur:
        # Users indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        print("✅ idx_users_email")
        
        # Books indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_books_title ON books(book_title)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_books_author ON books(author)")
        print("✅ idx_books_title, idx_books_author")
        
        # User books indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_books_user_id ON user_books(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_books_list_type ON user_books(list_type)")
        print("✅ idx_user_books_user_id, idx_user_books_list_type")
        
        # User activity indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_created_at ON user_activity(created_at DESC)")
        print("✅ idx_user_activity_user_id, idx_user_activity_created_at")
        
        # Refresh tokens indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id)")
        print("✅ idx_refresh_tokens_token, idx_refresh_tokens_user_id")
        
        # Password reset tokens indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_user_id ON password_reset_tokens(user_id)")
        print("✅ idx_password_reset_user_id")
        
        # Quiz scores indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_quiz_scores_user_id ON quiz_scores(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_quiz_scores_created_at ON quiz_scores(created_at DESC)")
        print("✅ idx_quiz_scores_user_id, idx_quiz_scores_created_at")
        
        # Subscriptions indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_is_active ON subscriptions(is_active)")
        print("✅ idx_subscriptions_user_id, idx_subscriptions_is_active")
        
        conn.commit()
    
    return True

def verify_schema(conn):
    """Verify all tables were created"""
    print_header("VERIFYING SCHEMA")
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        expected_tables = [
            'books', 'password_reset_tokens', 'quiz_scores', 
            'refresh_tokens', 'subscriptions', 'user_activity',
            'user_books', 'user_reading_profile', 'users'
        ]
        
        created_tables = [t[0] for t in tables]
        
        print("\n📊 Tables created:")
        for table in expected_tables:
            status = "✅" if table in created_tables else "❌"
            print(f"   {status} {table}")
        
        # Get row counts
        print("\n📈 Row counts:")
        for table in expected_tables:
            if table in created_tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"   📊 {table}: {count} rows")
    
    return True

def main():
    print_header("LITSCHOLAR DATABASE SCHEMA SETUP")
    
    # Get connection
    conn = get_db_connection()
    if not conn:
        sys.exit(1)
    
    try:
        # Confirm with user
        print("\n⚠️ This will create all tables for LitScholar")
        print("Tables to create:")
        print("   - users")
        print("   - books")
        print("   - user_reading_profile")
        print("   - user_books")
        print("   - user_activity")
        print("   - quiz_scores")
        print("   - refresh_tokens")
        print("   - password_reset_tokens")
        print("   - subscriptions")
        
        response = input("\n✅ Proceed with schema creation? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Cancelled")
            return
        
        # Create schema
        if not create_schema(conn):
            print("❌ Failed to create schema")
            return
        
        # Create indexes
        if not create_indexes(conn):
            print("❌ Failed to create indexes")
            return
        
        # Verify schema
        verify_schema(conn)
        
        print_header("SCHEMA CREATION COMPLETE")
        print("✅ All tables and indexes created successfully!")
        print("\n💡 Next steps:")
        print("   1. Insert books: cd FAISS_data_preprocessing && python insert_books_to_neon.py")
        print("   2. Start the FastAPI server")
        
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