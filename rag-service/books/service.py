import asyncpg
import json
import asyncio
from typing import List, Optional, Dict, Any
from datetime import date

from books.schemas import Book, RecommendedBook, GenreSection, UserBookResponse, RecommendedSectionsResponse
from retrieval.neon_fetch import fetch_books_by_ids
from retrieval.retriever import retrieve_books
from llm.gemini_client import ask_gemini

class BookService:
    def __init__(self, db: asyncpg.Connection):
        self.db = db
        print("✅ BookService initialized")

    # ============ HELPER METHODS ============
    
    async def fetch_books_by_ids(self, book_ids: List[str]) -> List[dict]:
        """Fetch book details by IDs using external function"""
        return await fetch_books_by_ids(book_ids)

    async def _enrich_with_summaries(self, books_data: List[dict]) -> List[dict]:
        """Add summaries to books from book_summary table"""
        if not books_data:
            return books_data
        
        book_ids = [b["book_id"] for b in books_data]
        
        # Fetch all summaries at once
        rows = await self.db.fetch(
            "SELECT book_id, summary FROM book_summary WHERE book_id = ANY($1::text[])",
            book_ids
        )
        
        summary_map = {row["book_id"]: row["summary"] for row in rows}
        
        for book in books_data:
            book["summary"] = summary_map.get(book["book_id"])
        
        return books_data

    async def _get_popular_fallback(self, limit: int, offset: int = 0) -> List[RecommendedBook]:
        """Fallback to popular books when recommendations fail"""
        print(f"Using popular books fallback (offset={offset}, limit={limit})")
        popular_ids = await self.get_popular_book_ids(offset=offset, limit=limit)
        if popular_ids:
            books_data = await self.fetch_books_by_ids(popular_ids)
            books_data = await self._enrich_with_summaries(books_data)
            return [RecommendedBook(**b) for b in books_data]
        return []

    async def _process_search_results(
        self,
        search_results: List[dict],
        user_history: List[asyncpg.Record],
        limit: int,
        source: str
    ) -> List[RecommendedBook]:
        """Process search results and filter out viewed books"""
        try:
            # Get IDs of books user has already seen
            viewed_ids = [str(r["book_id"]) for r in user_history] if user_history else []
            
            # Collect similar books, excluding already viewed ones
            similar_book_ids = []
            for result in search_results:
                if result["book_id"] not in viewed_ids and result["book_id"] not in similar_book_ids:
                    similar_book_ids.append(result["book_id"])
                    if len(similar_book_ids) >= limit:
                        break
            
            if not similar_book_ids:
                print(f"No {source} recommendations found")
                return []
            
            # Fetch book details
            books_data = await self.fetch_books_by_ids(similar_book_ids)

            # If nothing came back from Neon (e.g. books table empty or IDs mismatch),
            # fall back to popular so the user still sees something.
            if not books_data:
                print(f"⚠️ No book rows fetched for {source} IDs, using popular fallback")
                return await self._get_popular_fallback(limit)

            books_data = await self._enrich_with_summaries(books_data)
            print(f"✅ Found {len(books_data)} {source} recommendations")
            
            return [RecommendedBook(**b) for b in books_data]
            
        except Exception as e:
            print(f"Error processing search results: {e}")
            return []

    async def _process_search_results_with_pagination(
        self,
        search_results: List[dict],
        user_history: List[asyncpg.Record],
        offset: int,
        limit: int,
        source: str
    ) -> List[RecommendedBook]:
        """Process search results with pagination"""
        try:
            # Get IDs of books user has already seen
            viewed_ids = [str(r["book_id"]) for r in user_history] if user_history else []
            
            # Collect all similar books (excluding viewed)
            all_similar_ids = []
            for result in search_results:
                if result["book_id"] not in viewed_ids and result["book_id"] not in all_similar_ids:
                    all_similar_ids.append(result["book_id"])
            
            if not all_similar_ids:
                print(f"No {source} recommendations found")
                return []
            
            # Apply pagination
            start_idx = offset
            end_idx = start_idx + limit + 1  # Get one extra for hasMore
            paginated_ids = all_similar_ids[start_idx:end_idx]
            
            if not paginated_ids:
                return []
            
            # Fetch book details
            books_data = await self.fetch_books_by_ids(paginated_ids)

            # If nothing came back from Neon, fall back to popular for this page
            if not books_data:
                print(f"⚠️ No book rows fetched for {source} page, using popular fallback")
                page_index = offset // limit
                return await self._get_popular_fallback(limit, offset=page_index * limit)

            books_data = await self._enrich_with_summaries(books_data)
            print(f"✅ Found {len(books_data)} {source} recommendations (page {offset//limit + 1})")
            
            return [RecommendedBook(**b) for b in books_data]
            
        except Exception as e:
            print(f"Error processing paginated results: {e}")
            return []

    # ============ BASIC BOOK OPERATIONS ============

    async def get_book_by_id(self, book_id: str) -> Optional[Book]:
        """Get a single book by its ID"""
        try:
            books = await self.fetch_books_by_ids([book_id])
            if books:
                book_data = books[0]
                # Fetch summary from book_summary table
                summary_row = await self.db.fetchrow(
                    "SELECT summary FROM book_summary WHERE book_id = $1",
                    str(book_id)
                )
                if summary_row:
                    book_data["summary"] = summary_row["summary"]
                else:
                    book_data["summary"] = None
                return Book(**book_data)
            return None
        except Exception as e:
            print(f"Error in get_book_by_id: {e}")
            return None

    async def get_book_summary(self, book_id: str) -> Optional[str]:
        """Get or generate book summary"""
        try:
            # Check if summary exists
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
                return "Summary not available for this book."
                
            print(f"✨ Generating summary for: {book_row['book_title']}")
            prompt = f"""Write a 120-150 word book summary with:
- Main premise (2-3 sentences)
- Key themes (2-3 themes)
- Central ideas (1-2 sentences)

Book: "{book_row['book_title']}" by {book_row['author']}
Genre: {book_row.get('genres', '')}

Description: {book_row.get('book_details', '')}

Summary:"""
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(None, ask_gemini, prompt)
            
            if summary and "ERROR:" not in summary:
                # Save summary
                await self.db.execute(
                    "INSERT INTO book_summary (book_id, summary) VALUES ($1, $2) ON CONFLICT (book_id) DO UPDATE SET summary = $2",
                    str(book_id),
                    summary
                )
                return summary
            
            return "Summary not available at this moment."
            
        except Exception as e:
            print(f"❌ Error in get_book_summary: {e}")
            return "Summary not available due to a technical error."

    # ============ USER BOOK INTERACTIONS ============
    
    async def track_book_view(self, user_id: int, book_id: str) -> dict:
        """Track user book view/click"""
        try:
            uid = user_id
            bid = str(book_id)
        except Exception as e:
            raise ValueError(f"Invalid ID format: {e}")

        try:
            # Check if view exists
            existing = await self.db.fetchrow(
                "SELECT id, click_count FROM user_book_views WHERE user_id = $1 AND book_id = $2",
                uid, bid
            )

            if existing:
                # Update existing
                result = await self.db.fetchrow("""
                    UPDATE user_book_views
                    SET click_count = click_count + 1, last_viewed = NOW()
                    WHERE user_id = $1 AND book_id = $2
                    RETURNING click_count
                """, uid, bid)
                click_count = result["click_count"]
            else:
                # Insert new
                result = await self.db.fetchrow("""
                    INSERT INTO user_book_views(user_id, book_id, click_count, first_viewed, last_viewed)
                    VALUES($1, $2, 1, NOW(), NOW())
                    RETURNING click_count
                """, uid, bid)
                click_count = result["click_count"]

            # Log activity
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

    async def add_user_book(self, user_id: int, book_id: str, list_type: str, rating: int = None, notes: str = None) -> dict:
        """Add book to user's list"""
        try:
            uid = user_id
            bid = str(book_id)
            
            # Check if already exists
            existing = await self.db.fetchrow(
                "SELECT id FROM user_books WHERE user_id = $1 AND book_id = $2 AND list_type = $3",
                uid, bid, list_type
            )
            
            if existing:
                # Idempotent: treat "already present" as success
                return {"success": True, "message": f"Book already in {list_type} list"}
            
            # Insert
            result = await self.db.fetchrow("""
                INSERT INTO user_books (user_id, book_id, list_type, rating, notes, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                RETURNING id
            """, uid, bid, list_type, rating, notes)
            
            # If finished, update reading profile
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
            
            return {"success": True, "message": f"Book added to {list_type} list", "id": result["id"]}
            
        except Exception as e:
            print(f"Error in add_user_book: {str(e)}")
            return {"success": False, "message": str(e)}

    async def get_user_books(self, user_id: int, list_type: str = None, limit: int = 50) -> List[UserBookResponse]:
        """Get user's books by list type"""
        try:
            uid = user_id
            
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

    # ============ 4 CORE RECOMMENDATION METHODS ============

    # 1. FOR YOU - Personalized recommendations based on user history
    async def get_for_you_recommendations(
        self,
        user_id: int,
        limit: int = 8
    ) -> List[RecommendedBook]:
        """
        Get personalized recommendations based on user's viewed books
        Uses content-based similarity with STRICT threshold (score >= 0.7)
        """
        try:
            uid = user_id
            
            print(f"🔍 Getting FOR YOU recommendations for user {uid}")
            
            # Get user's viewed books
            user_history = await self.db.fetch(
                "SELECT book_id FROM user_book_views WHERE user_id = $1 ORDER BY last_viewed DESC LIMIT 3",
                uid
            )
            
            if not user_history:
                print("No user history - returning popular books")
                return await self._get_popular_fallback(limit)
            
            # Get details of their most recent viewed book
            recent_book_id = user_history[0]["book_id"]
            book_row = await self.db.fetchrow(
                "SELECT book_title, author, genres, book_details FROM books WHERE book_id = $1",
                str(recent_book_id)
            )
            
            if not book_row:
                return await self._get_popular_fallback(limit)
            
            # Create search query from the book they viewed
            query_text = f"{book_row['book_title']} {book_row['author']} {book_row.get('genres', '')}"
            print(f"🔎 Finding books similar to: {book_row['book_title']}")
            
            # Get MORE results from Chroma (3x limit) so we have enough to filter
            search_results = retrieve_books(query_text, top_k=limit * 3)
            
            if not search_results:
                return await self._get_popular_fallback(limit)
            
            # FOR YOU: Use STRICT threshold (score >= 0.7) for highly relevant books
            filtered_results = [
                r for r in search_results 
                if r["score"] >= 0.7  # STRICT threshold (distance <= 0.3)
            ]
            
            print(f"Strict threshold (score >= 0.7): {len(filtered_results)} books")
            
            # If no results with strict threshold, try medium threshold
            if len(filtered_results) < limit:
                print("Not enough strict matches, using medium threshold (score >= 0.5)")
                filtered_results = [
                    r for r in search_results 
                    if r["score"] >= 0.5  # MEDIUM threshold (distance <= 0.5)
                ]
            
            return await self._process_search_results(
                filtered_results, 
                user_history, 
                limit,
                "for-you"
            )
            
        except Exception as e:
            print(f"❌ Error in get_for_you_recommendations: {e}")
            return await self._get_popular_fallback(limit)

    # 2. POPULAR - Trending books based on views
    async def get_popular_book_ids(self, offset: int = 0, limit: int = 8) -> List[str]:
        """Get popular book IDs based on views"""
        try:
            # Try to get books with most views
            query = """
                SELECT book_id, SUM(click_count) as popularity
                FROM user_book_views
                GROUP BY book_id
                ORDER BY popularity DESC
                OFFSET $1 LIMIT $2
            """
            rows = await self.db.fetch(query, offset, limit)
            if rows:
                book_ids = [str(row["book_id"]) for row in rows]
                print(f'Found {len(book_ids)} popular books with views')
                return book_ids
            
            # If no views, return random books with OFFSET for pagination
            print('No views found, returning random books')
            random_query = """
                SELECT book_id 
                FROM books 
                WHERE book_id IS NOT NULL 
                ORDER BY RANDOM()
                OFFSET $1 LIMIT $2
            """
            random_rows = await self.db.fetch(random_query, offset, limit)
            book_ids = [str(row["book_id"]) for row in random_rows]
            print(f'Returning {len(book_ids)} random books from offset {offset}')
            return book_ids
            
        except Exception as e:
            print(f"Error getting popular books: {e}")
            return []

    async def get_popular_recommendations(
        self,
        limit: int = 8
    ) -> List[RecommendedBook]:
        """Get popular/trending books"""
        try:
            popular_ids = await self.get_popular_book_ids(offset=0, limit=limit)
            if popular_ids:
                books_data = await self.fetch_books_by_ids(popular_ids)
                books_data = await self._enrich_with_summaries(books_data)
                return [RecommendedBook(**b) for b in books_data]
            return []
        except Exception as e:
            print(f"Error in get_popular_recommendations: {e}")
            return []

    # 3. BY GENRE - Books grouped by genre
    async def get_genre_recommendations(
        self,
        genres_limit: int = 6,
        books_per_genre: int = 4
    ) -> List[GenreSection]:
        """Get books grouped by genre"""
        try:
            genre_sections = []
            
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
                    books_data = await self.fetch_books_by_ids(book_ids)
                    books_data = await self._enrich_with_summaries(books_data)
                    genre_books = [RecommendedBook(**b) for b in books_data]
                    genre_sections.append(GenreSection(genre=genre, books=genre_books))
            
            print(f"📚 Found {len(genre_sections)} genre sections")
            return genre_sections
            
        except Exception as e:
            print(f"Error getting genre sections: {e}")
            return []

    # 4. SIMILAR - Similar books with pagination and progressive thresholds
    async def get_similar_recommendations(
        self,
        user_id: int,
        page: int = 1,
        limit: int = 8
    ) -> List[RecommendedBook]:
        """
        Get similar books using Chroma retrieval with progressive thresholds
        Threshold INCREASES with page number to get more results
        """
        try:
            uid = user_id
            offset = (page - 1) * limit
            
            print(f"🔍 Getting SIMILAR recommendations for user {uid}, page {page}")
            
            # Get user's recently viewed book
            user_history = await self.db.fetch(
                "SELECT book_id FROM user_book_views WHERE user_id = $1 ORDER BY last_viewed DESC LIMIT 1",
                uid
            )
            
            if not user_history:
                return await self._get_popular_fallback(limit, offset)
            
            recent_book_id = user_history[0]["book_id"]
            book_row = await self.db.fetchrow(
                "SELECT book_title, author, genres, book_details FROM books WHERE book_id = $1",
                str(recent_book_id)
            )
            
            if not book_row:
                return await self._get_popular_fallback(limit, offset)
            
            # Create search query
            query_text = f"{book_row['book_title']} {book_row['author']} {book_row.get('genres', '')}"
            
            # Get MANY results from Chroma (enough for all pages)
            total_needed = (page + 2) * limit
            search_results = retrieve_books(query_text, top_k=total_needed)
            
            if not search_results:
                return await self._get_popular_fallback(limit, offset)
            
            # SIMILAR: Use PROGRESSIVE thresholds based on page number
            # Convert distance thresholds to score thresholds
            if page == 1:
                min_score = 0.6  # distance <= 0.4
            elif page == 2:
                min_score = 0.5  # distance <= 0.5
            else:
                min_score = 0.4  # distance <= 0.6 (pages 3 and beyond)
            
            print(f"Page {page} using min_score: {min_score}")
            
            filtered_results = [
                r for r in search_results 
                if r["score"] >= min_score
            ]
            
            print(f"Found {len(filtered_results)} books with score >= {min_score}")
            
            # If no results with current threshold, try next threshold
            if len(filtered_results) < offset + limit:
                next_min_score = max(min_score - 0.1, 0.2)
                print(f"Not enough results, trying min_score: {next_min_score}")
                filtered_results = [
                    r for r in search_results 
                    if r["score"] >= next_min_score
                ]
            
            return await self._process_search_results_with_pagination(
                filtered_results,
                user_history,
                offset,
                limit,
                f"similar-page{page}"
            )
            
        except Exception as e:
            print(f"❌ Error in similar recommendations: {e}")
            return await self._get_popular_fallback(limit, offset)

    # ============ ADDITIONAL METHODS ============

    async def get_all_recommendation_sections(
        self,
        user_id: int,
        for_you_limit: int = 6,
        popular_limit: int = 12,
        genres_limit: int = 6,
        books_per_genre: int = 4,
    ) -> RecommendedSectionsResponse:
        """Return structured sections with all recommendations"""
        try:
            print(f"📑 Getting all recommendation sections for user {user_id}")
            
            # Get for you section
            for_you_books = await self.get_for_you_recommendations(
                user_id=user_id,
                limit=for_you_limit
            )
            print(f"✨ For you: {len(for_you_books)} books")
            
            # Get popular books
            popular_books = await self.get_popular_recommendations(
                limit=popular_limit
            )
            print(f"🔥 Popular: {len(popular_books)} books")
            
            # Get genre sections
            by_genre = await self.get_genre_recommendations(
                genres_limit=genres_limit,
                books_per_genre=books_per_genre
            )
            print(f"📚 Genre sections: {len(by_genre)} genres")

            return RecommendedSectionsResponse(
                for_you=for_you_books,
                popular=popular_books,
                by_genre=by_genre
            )
            
        except Exception as e:
            print(f"Error in get_all_recommendation_sections: {e}")
            return RecommendedSectionsResponse(
                for_you=[], 
                popular=[], 
                by_genre=[]
            )

    # ============ ASSISTANT SEARCH ============

    async def search_books_assistant(
        self,
        query: str,
        limit: int = 6
    ) -> List[RecommendedBook]:
        """
        Search books for AI assistant
        Uses GENEROUS threshold (score >= 0.3) to get many results
        """
        try:
            print(f"🔎 Assistant searching for: {query}")
            
            # Get many results from Chroma
            search_results = retrieve_books(query, top_k=limit * 3)
            
            if not search_results:
                return []
            
            # ASSISTANT: Use GENEROUS threshold (score >= 0.3)
            filtered_results = [
                r for r in search_results 
                if r["score"] >= 0.3  # distance <= 0.7
            ]
            
            # Take top results
            top_results = filtered_results[:limit]
            
            # Extract book IDs
            book_ids = [r["book_id"] for r in top_results]
            
            # Fetch book details
            books_data = await self.fetch_books_by_ids(book_ids)
            books_data = await self._enrich_with_summaries(books_data)
            return [RecommendedBook(**b) for b in books_data]
            
        except Exception as e:
            print(f"❌ Error in assistant search: {e}")
            return []
