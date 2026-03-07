from pathlib import Path
import csv
import asyncpg
import os
import httpx
import asyncio


CSV_PATH = 'data/books_clean.csv'

DB_URL = os.getenv('DB_URL_NEON')

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = 'mistral'

BATCH_SIZE = 20


# OLLAMA Summary

async def summarize_book(client,title,author,genere,book_detail):
    prompt = f""" 
     Summarize this book in 150 words including theme of the book.
     As the book data i have is not sufficient for books summary so u need to also find data from urself fro summary
     Title : {title}
     Author : {author}
     Genere : {genere}
     Detail : {book_detail}
    """
    
    response = await client.post(
        OLLAMA_URL,
        json={
            'model' : OLLAMA_MODEL,
            'prompt' : prompt,
            'stream' : False
        },
        timeout = 180
    )
    
    data = response.json()
    return data['response']


# Load the books from csv 
def load_books_from_csv():
    print('Loading books from local csv')
    
    books = []
    
    with open(CSV_PATH,encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            books.append({
                'book_id' : row['book_id'],
                'title' : row['book_title'],
                'author' : row['author'],
                'genere' : row['generes'],
                'detail' : row['book_details']
            })
        return books
    
# Load books form neon
async def load_books_from_neon(conn):
    print('Loading books from Neaon DB')
    
    rows = await conn.fetch(
    """
        SELECT book_id , book_title , author , generes , book_details
        FROM books 
        WHERE summary IS NULL
    """
    )
    
    books = []
    for row in rows:
        books.append({
                'book_id' : row['book_id'],
                'title' : row['book_title'],
                'author' : row['author'],
                'genere' : row['generes'],
                'detail' : row['book_details']
            })
    return books
    
    
# Process book
async def process_book(conn,client,book):
    summary = await summarize_book(
        client,
        book['title'],
        book['author'],
        book['genere'],
        book['detail']
    )
    
    await conn.execute(
        """
        UPDATE books SET summary = $1 
        WHERE book_id = $2
        """,
        summary,
        book['book_id'])
    
async def main():
    print("\n Litscholar - Book summarization pipeline \n")
    
    conn = await asyncpg.connect(DB_URL)
    
    # decide data source
    if CSV_PATH.exists():
        books = load_books_from_csv()
    else:
        books = await load_books_from_neon(conn)
    
    print(f'Books to summarize : {len(books)}')
    
    async with httpx.AsyncClient() as client:
        for i in range(0,len(books),BATCH_SIZE):
            batch = books[i:1+BATCH_SIZE]
            tasks = [
                process_book(conn, client, b)
                for b in batch
            ]
            await asyncio.gather(*tasks)
    await conn.close()
    
    print("\n Summarization completed\n")
    
if __name__ == "__main__":
    asyncio.run(main())