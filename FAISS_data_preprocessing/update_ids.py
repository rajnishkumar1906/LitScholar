"""
generate_unique_ids.py - Creates truly unique book IDs
Methods: UUID, timestamp-based, hash-based, or random
"""

import csv
import uuid
import random
import string
import hashlib
from datetime import datetime

def generate_uuid_based(book_title, author, counter=None):
    """Generate UUID-based unique ID (most unique)"""
    return f"BK-{uuid.uuid4().hex[:8].upper()}"

def generate_timestamp_based(counter):
    """Generate timestamp-based unique ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(1000, 9999)
    return f"BK-{timestamp}-{random_num}"

def generate_hash_based(book_title, author, counter):
    """Generate hash-based unique ID from book data"""
    data = f"{book_title}{author}{counter}{datetime.now()}".encode()
    hash_val = hashlib.md5(data).hexdigest()[:8].upper()
    return f"BK-{hash_val}"

def generate_random_based(counter):
    """Generate random alphanumeric unique ID"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=8))
    return f"BK-{random_part}"

def generate_sequential_with_hash(counter):
    """Sequential but with hash suffix for uniqueness"""
    hash_part = hashlib.md5(str(counter).encode()).hexdigest()[:4].upper()
    return f"BK{str(counter).zfill(6)}-{hash_part}"

def main():
    print("\n" + "="*60)
    print("📚 TRULY UNIQUE BOOK ID GENERATOR")
    print("="*60)
    
    # Check if file exists
    input_file = 'books_clean.csv'
    if not __import__('os').path.exists(input_file):
        print(f"\n❌ Error: {input_file} not found!")
        return
    
    # Choose ID type
    print("\n🔑 Choose ID Generation Method:")
    print("  1. UUID-based (e.g., BK-A3F9E2C1) - Most unique")
    print("  2. Timestamp-based (e.g., BK-20260112-143022-5821)")
    print("  3. Hash-based from book data (e.g., BK-8F3A9E2C)")
    print("  4. Random 8-char (e.g., BK-K9M3N7P2)")
    print("  5. Sequential with hash (e.g., BK016157-4A8F)")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    # Get prefix
    prefix = input("Enter prefix (press Enter for 'BK'): ").strip()
    if not prefix:
        prefix = "BK"
    else:
        prefix = prefix.upper()
    
    # Read data
    print(f"\n📖 Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    total = len(rows)
    print(f"📦 Found {total} books")
    
    # Generate timestamp for output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'books_clean_unique_ids_{timestamp}.csv'
    
    # Generate new IDs based on choice
    print(f"\n🔄 Generating unique IDs...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for idx, row in enumerate(rows, 1):
            old_id = row['book_id']
            book_title = row.get('book_title', '')
            author = row.get('author', '')
            
            # Generate new ID based on choice
            if choice == '1':
                new_id = generate_uuid_based(book_title, author, idx)
            elif choice == '2':
                new_id = generate_timestamp_based(idx)
            elif choice == '3':
                new_id = generate_hash_based(book_title, author, idx)
            elif choice == '4':
                new_id = generate_random_based(idx)
            elif choice == '5':
                new_id = generate_sequential_with_hash(idx)
            else:
                new_id = generate_uuid_based(book_title, author, idx)
            
            # Add prefix
            if not new_id.startswith(prefix):
                new_id = f"{prefix}-{new_id.replace(prefix, '').lstrip('-')}"
            
            row['book_id'] = new_id
            writer.writerow(row)
            
            # Show first 5 examples
            if idx <= 5:
                print(f"   {old_id} → {new_id}")
        
        if total > 5:
            print(f"   ... and {total - 5} more")
    
    print("\n" + "="*60)
    print("✅ SUCCESS! Unique IDs generated")
    print("="*60)
    print(f"📁 New file: {output_file}")
    print(f"📊 Total books: {total}")
    print(f"🔑 ID Type: ", end="")
    if choice == '1': print("UUID-based (globally unique)")
    elif choice == '2': print("Timestamp-based")
    elif choice == '3': print("Hash-based from book data")
    elif choice == '4': print("Random 8-character")
    else: print("Sequential with hash suffix")
    
    print(f"\n💡 To use this file, rename it to 'books_clean.csv'")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()