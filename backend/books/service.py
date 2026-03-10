import asyncpg
import json
import random
import asyncio
from typing import List, Optional, Dict, Any
from datetime import date
from books.schemas import Book, RecommendedBook, GenreSection, RecommendedSectionsResponse, UserBookResponse
from retrieval.neon_fetch import fetch_books_by_ids
from llm.gemini_client import ask_gemini

class BookService:
    def __init__(self, db: asyncpg.Connection):
        self.db = db
        print("✅ BookService initialized")
    
    async def get_book_by_id(self, book_id: str) -> Optional[Book]:
        try:
            books = await fetch_books_by_ids([book_id])
            if books:
                return Book(**books[0])
            return None
        except Exception as e:
            print(f"Error in get_book_by_id: {e}")
            return None

    async def get_book_summary(self, book_id: str) -> Optional[str]:
        try:
            # Check if summary exists in book_summary table
            row = await self.db.fetchrow(
                "SELECT summary FROM book_summary WHERE book_id = $1",
                str(book_id)
            )
            
            if row and row["summary"]:
                return row["summary"]
            
            # Get book details
            book_row = await self.db.fetchrow(
                "SELECT book_title, author, genres, book_details FROM books WHERE book_id = $1",
                str(book_id)
            )
            
            if not book_row:
                print(f"❌ Book with ID {book_id} not found in database.")
                return "Summary not available for this book."
                
            print(f"✨ Generating on-demand summary for: {book_row['book_title']}")
            prompt = f"""
Write a concise 120–150 word summary of this book.
Include the theme, major ideas, and overall premise.

Title: {book_row['book_title']}
Author: {book_row['author']}
Genre: {book_row.get('genres', '')}

Description:
{book_row.get('book_details', '')}
"""
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(None, ask_gemini, prompt)
            
            if summary and "ERROR:" not in summary:
                # Save to book_summary table
                await self.db.execute(
                    "INSERT INTO book_summary (book_id, summary) VALUES ($1, $2) ON CONFLICT (book_id) DO UPDATE SET summary = $2",
                    str(book_id),
                    summary
                )
                print(f"✅ On-demand summary saved for: {book_row['book_title']}")
                return summary
            
            return "Summary not available at this moment. Please try again later."
            
        except Exception as e:
            print(f"❌ Error in get_book_summary: {e}")
            return "Summary not available due to a technical error."
    
    async def track_book_view(self, user_id: str, book_id: str) -> dict:
        """Track user book view/click with count and timestamp."""
        try:
            uid = int(user_id)
            bid = str(book_id)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid ID format: {e}")

        try:
            # Check if view exists
            check_query = """
                SELECT id, click_count FROM user_book_views
                WHERE user_id = $1 AND book_id = $2
            """
            existing = await self.db.fetchrow(check_query, uid, bid)

            if existing:
                # Update existing
                update_query = """
                UPDATE user_book_views
                SET click_count = click_count + 1, last_viewed = NOW()
                WHERE user_id = $1 AND book_id = $2
                RETURNING click_count
                """
                result = await self.db.fetchrow(update_query, uid, bid)
                click_count = result["click_count"]
            else:
                # Insert new
                insert_query = """
                INSERT INTO user_book_views(user_id, book_id, click_count, first_viewed, last_viewed)
                VALUES($1, $2, 1, NOW(), NOW())
                RETURNING click_count
                """
                result = await self.db.fetchrow(insert_query, uid, bid)
                click_count = result["click_count"]

            # Also log to user_activity
            await self.db.execute("""
                INSERT INTO user_activity (user_id, activity_type, book_id, metadata, created_at)
                VALUES ($1, $2, $3, $4, NOW())
            """, uid, 'book_click', bid, json.dumps({"action": "view", "click_count": click_count}))
            
            return {
                "success": True,
                "book_id": book_id,
                "click_count": click_count
            }
            
        except Exception as e:
            print(f"Error in track_book_view: {str(e)}")
            raise

    async def add_user_book(self, user_id: str, book_id: str, list_type: str, rating: int = None, notes: str = None) -> dict:
        """Add book to user's list (wishlist, reading, finished)"""
        try:
            uid = int(user_id)
            bid = str(book_id)
            
            # Check if already exists
            existing = await self.db.fetchrow(
                "SELECT id FROM user_books WHERE user_id = $1 AND book_id = $2 AND list_type = $3",
                uid, bid, list_type
            )
            
            if existing:
                return {"success": False, "message": f"Book already in {list_type} list"}
            
            # Insert
            result = await self.db.fetchrow("""
                INSERT INTO user_books (user_id, book_id, list_type, rating, notes, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                RETURNING id
            """, uid, bid, list_type, rating, notes)
            
            # If finished, update user_reading_profile
            if list_type == 'finished':
                await self.db.execute("""
                    INSERT INTO user_reading_profile (user_id, total_books_read, last_read_date, updated_at)
                    VALUES ($1, 1, NOW(), NOW())
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        total_books_read = user_reading_profile.total_books_read + 1,
                        last_read_date = NOW(),
                        updated_at = NOW()
                """, uid)
            
            # Log activity
            await self.db.execute("""
                INSERT INTO user_activity (user_id, activity_type, book_id, metadata, created_at)
                VALUES ($1, $2, $3, $4, NOW())
            """, uid, f'book_{list_type}', bid, json.dumps({"rating": rating}))
            
            return {"success": True, "id": result["id"]}
            
        except Exception as e:
            print(f"Error in add_user_book: {e}")
            return {"success": False, "message": str(e)}

    async def get_user_books(self, user_id: str, list_type: str = None, limit: int = 50) -> List[UserBookResponse]:
        """Get user's books by list type"""
        try:
            uid = int(user_id)
            
            if list_type:
                rows = await self.db.fetch("""
                    SELECT * FROM user_books 
                    WHERE user_id = $1 AND list_type = $2
                    ORDER BY created_at DESC
                    LIMIT $3
                """, uid, list_type, limit)
            else:
                rows = await self.db.fetch("""
                    SELECT * FROM user_books 
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, uid, limit)
            
            return [UserBookResponse(**dict(row)) for row in rows]
            
        except Exception as e:
            print(f"Error in get_user_books: {e}")
            return []

    async def _get_popular_books(self, limit: int) -> List[str]:
        """Get popular book IDs from user_book_views"""
        try:
            query = """
                SELECT book_id, SUM(click_count) as popularity
                FROM user_book_views
                GROUP BY book_id
                ORDER BY popularity DESC
                LIMIT $1
            """
            rows = await self.db.fetch(query, limit)
            if rows:
                return [str(row["book_id"]) for row in rows]
            
            # If no views, return random books
            random_query = "SELECT book_id FROM books ORDER BY RANDOM() LIMIT $1"
            random_rows = await self.db.fetch(random_query, limit)
            return [str(row["book_id"]) for row in random_rows]
            
        except Exception as e:
            print(f"Error getting popular books: {e}")
            return []

    async def get_hybrid_recommendations(
        self,
        user_id: str,
        limit: int = 8
    ) -> List[RecommendedBook]:
        """Get recommendations based on user history"""
        try:
            uid = int(user_id)
            
            # Check if user has history
            has_history = await self.db.fetchval(
                "SELECT EXISTS(SELECT 1 FROM user_book_views WHERE user_id = $1)",
                uid
            )
            
            if not has_history:
                print(f"👤 User {uid} has no history - returning popular books")
                popular_ids = await self._get_popular_books(limit)
                if popular_ids:
                    books_data = await fetch_books_by_ids(popular_ids)
                    return [RecommendedBook(**b) for b in books_data]
            
            # Get user's viewed books
            user_history = await self.db.fetch(
                "SELECT book_id FROM user_book_views WHERE user_id = $1 ORDER BY click_count DESC LIMIT 10",
                uid
            )
            user_book_ids = [row["book_id"] for row in user_history]
            
            # Collaborative: find books viewed by users who viewed same books
            if user_book_ids:
                similar_users_query = """
                    SELECT DISTINCT user_id
                    FROM user_book_views
                    WHERE book_id = ANY($1::text[]) AND user_id != $2
                    LIMIT 20
                """
                similar_users = await self.db.fetch(similar_users_query, user_book_ids, uid)
                similar_user_ids = [row["user_id"] for row in similar_users]
                
                if similar_user_ids:
                    rec_query = """
                        SELECT DISTINCT book_id
                        FROM user_book_views
                        WHERE user_id = ANY($1::int[])
                        AND book_id != ALL($2::text[])
                        GROUP BY book_id
                        ORDER BY SUM(click_count) DESC
                        LIMIT $3
                    """
                    rec_ids = await self.db.fetch(rec_query, similar_user_ids, user_book_ids, limit)
                    if rec_ids:
                        book_ids = [str(row["book_id"]) for row in rec_ids]
                        books_data = await fetch_books_by_ids(book_ids)
                        return [RecommendedBook(**b) for b in books_data]
            
            # Fallback to popular
            popular_ids = await self._get_popular_books(limit)
            if popular_ids:
                books_data = await fetch_books_by_ids(popular_ids)
                return [RecommendedBook(**b) for b in books_data]
            
            # Ultimate fallback - random books
            random_ids = await self.db.fetch(
                "SELECT book_id FROM books ORDER BY RANDOM() LIMIT $1",
                limit
            )
            book_ids = [str(r["book_id"]) for r in random_ids]
            books_data = await fetch_books_by_ids(book_ids)
            return [RecommendedBook(**b) for b in books_data]
            
        except Exception as e:
            print(f"❌ Error in hybrid recommendations: {e}")
            return []

    async def get_recommended_sections(
        self,
        user_id: str,
        for_you_limit: int = 6,
        popular_limit: int = 12,
        genres_limit: int = 6,
        books_per_genre: int = 4,
    ) -> RecommendedSectionsResponse:
        """Return structured sections with recommendations"""
        try:
            # Get for you section
            for_you = await self.get_hybrid_recommendations(
                user_id=user_id,
                limit=for_you_limit
            )
            
            # Get popular books
            popular_ids = await self._get_popular_books(popular_limit)
            popular = []
            if popular_ids:
                books_data = await fetch_books_by_ids(popular_ids)
                popular = [RecommendedBook(**b) for b in books_data]
            
            # Get genre sections
            by_genre = []
            try:
                # Get unique genres
                genre_rows = await self.db.fetch("""
                    SELECT DISTINCT trim(unnest(string_to_array(genres, ','))) as genre
                    FROM books
                    WHERE genres IS NOT NULL AND genres != ''
                    LIMIT $1
                """, genres_limit)
                
                for genre_row in genre_rows:
                    genre = genre_row["genre"]
                    if not genre:
                        continue
                        
                    # Get books for this genre
                    book_rows = await self.db.fetch("""
                        SELECT book_id
                        FROM books
                        WHERE genres ILIKE $1
                        ORDER BY RANDOM()
                        LIMIT $2
                    """, f'%{genre}%', books_per_genre)
                    
                    if book_rows:
                        book_ids = [str(row["book_id"]) for row in book_rows]
                        books_data = await fetch_books_by_ids(book_ids)
                        genre_books = [RecommendedBook(**b) for b in books_data]
                        by_genre.append(GenreSection(genre=genre, books=genre_books))
                        
            except Exception as e:
                print(f"Error getting genre sections: {e}")

            return RecommendedSectionsResponse(
                for_you=for_you,
                popular=popular,
                by_genre=by_genre
            )
            
        except Exception as e:
            print(f"Error in get_recommended_sections: {e}")
            return RecommendedSectionsResponse(for_you=[], popular=[], by_genre=[])