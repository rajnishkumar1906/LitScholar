"""
insert_books_to_neon.py - Insert books from CSV to Neon database
Run from FAISS_data_preprocessing folder: python insert_books_to_neon.py
"""

import os
import csv
import sys
import psycopg
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from root folder
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_URL = os.getenv("DB_URL_NEON")
# USE YOUR UNIQUE IDS FILE
CSV_PATH = "books_clean_unique_ids_20260412_164626.csv"  # Updated to your unique IDs file

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
        conn = psycopg.connect(DB_URL)
        print("✅ Connected to Neon database")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def check_csv():
    """Check if CSV file exists and has data"""
    if not os.path.exists(CSV_PATH):
        print(f"\n❌ CSV file not found: {CSV_PATH}")
        print(f"📁 Available CSV files:")
        for file in os.listdir('.'):
            if file.endswith('.csv'):
                print(f"   - {file}")
        return False
    
    # Count rows
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"\n📊 Found {len(rows)} books in CSV")
    print(f"📝 First 3 IDs from CSV:")
    for i, row in enumerate(rows[:3]):
        print(f"   {i+1}. {row.get('book_id', 'NO ID')}")
    
    return rows

def clear_existing_data(conn):
    """Clear existing data from books table"""
    print_header("CLEARING EXISTING DATA")
    
    confirm = input("\n⚠️ Delete all existing books from database? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("❌ Cancelled - keeping existing data")
        return False
    
    with conn.cursor() as cur:
        try:
            cur.execute("DELETE FROM summaries")
            print("✅ Cleared summaries table")
        except:
            pass
        
        cur.execute("DELETE FROM books")
        print("✅ Cleared books table")
        conn.commit()
    
    return True

def insert_books(conn, books):
    """Insert books into database"""
    print_header("INSERTING BOOKS")
    
    insert_query = """
        INSERT INTO books (
            book_id, 
            book_title, 
            author, 
            genres, 
            book_details, 
            num_pages, 
            cover_image_url,
            created_at,
            updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (book_id) DO UPDATE SET
            book_title = EXCLUDED.book_title,
            author = EXCLUDED.author,
            genres = EXCLUDED.genres,
            book_details = EXCLUDED.book_details,
            num_pages = EXCLUDED.num_pages,
            cover_image_url = EXCLUDED.cover_image_url,
            updated_at = CURRENT_TIMESTAMP
    """
    
    inserted = 0
    errors = 0
    batch_size = 1000
    current_time = datetime.now()
    
    with conn.cursor() as cur:
        for i in range(0, len(books), batch_size):
            batch = books[i:i+batch_size]
            batch_data = []
            
            for book in batch:
                book_id = str(book.get('book_id', '')).strip()
                if not book_id:
                    errors += 1
                    continue
                
                num_pages = book.get('num_pages', '0')
                try:
                    num_pages = int(num_pages) if num_pages and str(num_pages).isdigit() else 0
                except:
                    num_pages = 0
                
                batch_data.append((
                    book_id,
                    book.get('book_title', '')[:500],
                    book.get('author', '')[:200],
                    book.get('genres', '')[:500],
                    book.get('book_details', ''),
                    num_pages,
                    book.get('cover_image_url', ''),
                    current_time,
                    current_time
                ))
            
            if batch_data:
                try:
                    cur.executemany(insert_query, batch_data)
                    conn.commit()
                    inserted += len(batch_data)
                    print(f"🔄 Inserted {inserted}/{len(books)} books")
                except Exception as e:
                    print(f"❌ Error inserting batch: {e}")
                    errors += len(batch_data)
    
    return inserted, errors

def verify_insertion(conn):
    """Verify books were inserted correctly"""
    print_header("VERIFYING INSERTION")
    
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM books")
        total = cur.fetchone()[0]
        print(f"📊 Total books in database: {total}")
        
        if total > 0:
            cur.execute("""
                SELECT book_id, book_title, author 
                FROM books 
                LIMIT 5
            """)
            samples = cur.fetchall()
            
            print("\n📝 Sample books inserted:")
            for i, sample in enumerate(samples, 1):
                print(f"   {i}. ID: {sample[0]} | Title: {sample[1][:50]} | Author: {sample[2]}")
            
            cur.execute("SELECT pg_typeof(book_id) FROM books LIMIT 1")
            id_type = cur.fetchone()[0]
            print(f"\n🔑 book_id data type: {id_type}")
        
        return total

def main():
    print_header("NEON DATABASE BOOK INSERTION")
    print(f"📁 CSV path: {CSV_PATH}")
    print(f"📁 Current directory: {os.getcwd()}")
    
    books = check_csv()
    if not books:
        return
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        response = input("\n🔄 Clear existing data before inserting? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            clear_existing_data(conn)
        
        inserted, errors = insert_books(conn, books)
        total = verify_insertion(conn)
        
        print_header("INSERTION COMPLETE")
        print(f"✅ Successfully inserted: {inserted} books")
        print(f"❌ Errors: {errors}")
        print(f"📊 Total in database: {total}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()