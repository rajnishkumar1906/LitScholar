import asyncpg
import json
import random
import asyncio
from typing import List, Optional, Dict, Any
from books.schemas import Book
from retrieval.neon_fetch import fetch_books_by_ids
from retrieval.retriever import search_books
from llm.gemini_client import ask_gemini

class BookService:
    def __init__(self, db: asyncpg.Connection):
        self.db = db
        print("✅ BookService initialized")
    
    async def get_book_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Get single book by ID"""
        try:
            books = await fetch_books_by_ids([book_id])
            return books[0] if books else None
        except Exception as e:
            print(f"Error in get_book_by_id: {e}")
            return None

    async def get_book_summary(self, book_id: str) -> Optional[str]:
        """Generate and save summary for a book if it doesn't exist"""
        try:
            # 1. Check if summary already exists in DB
            row = await self.db.fetchrow(
                "SELECT summary, book_title, author, genres, book_details FROM books WHERE book_id = $1",
                int(book_id)
            )
            
            if not row:
                return None
                
            if row["summary"]:
                return row["summary"]
                
            # 2. Generate on-demand if missing
            print(f"✨ Generating on-demand summary for: {row['book_title']}")
            prompt = f"""
Write a concise 120–150 word summary of this book.
Include the theme, major ideas, and overall premise.

Title: {row['book_title']}
Author: {row['author']}
Genre: {row.get('genres', '')}

Description:
{row.get('book_details', '')}
"""
            # Run the blocking ask_gemini in a thread to keep things async
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(None, ask_gemini, prompt)
            
            if summary and "ERROR:" not in summary:
                # Save to database
                await self.db.execute(
                    "UPDATE books SET summary = $1 WHERE book_id = $2",
                    summary,
                    int(book_id)
                )
                print(f"✅ On-demand summary saved for: {row['book_title']}")
                return summary
            
            return None
        except Exception as e:
            print(f"Error in get_book_summary: {e}")
            return None
    
    async def track_book_view(self, user_id: str, book_id: str) -> dict:
        """Track user book view/click with count and timestamp."""
        try:
            uid = int(user_id)
            # Convert book_id to integer for database
            bid = int(book_id)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid ID format: {e}")

        try:
            check_query = """
                SELECT id, click_count FROM user_book_views
                WHERE user_id = $1 AND book_id = $2
            """
            existing = await self.db.fetchrow(check_query, uid, bid)

            if existing:
                update_query = """
                UPDATE user_book_views
                SET click_count = click_count + 1, last_viewed = NOW()
                WHERE user_id = $1 AND book_id = $2
                """
                await self.db.execute(update_query, uid, bid)
                click_count = existing["click_count"] + 1
            else:
                insert_query = """
                INSERT INTO user_book_views(user_id, book_id, click_count, first_viewed, last_viewed)
                VALUES($1, $2, 1, NOW(), NOW())
                """
                await self.db.execute(insert_query, uid, bid)
                click_count = 1

            # Log activity
            activity_query = """
            INSERT INTO user_activity (user_id, activity_type, book_id, metadata, created_at)
            VALUES ($1, $2, $3, $4, NOW())
            """
            metadata = json.dumps({"action": "click", "click_count": click_count})
            await self.db.execute(activity_query, uid, 'book_click', bid, metadata)
            
            # Return book_id as string for API consistency
            return {
                "book_id": book_id,  # Return original string ID
                "click_count": click_count,
                "last_viewed": "now"
            }
            
        except Exception as e:
            print(f"Error in track_book_view: {str(e)}")
            raise

    async def get_combined_recommendations(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Personalized recommendations: uses this user's history first, then other users'
        experience (similar users), then genre match, then global popular.
        """
        try:
            uid = int(user_id)
        except (TypeError, ValueError):
            return []

        recommended_ids = []  # Will store string IDs for fetch_books_by_ids
        books_needed = limit

        try:
            # 1. Get user's history (book_ids are integers in DB)
            try:
                user_history_query = """
                SELECT book_id, click_count
                FROM user_book_views
                WHERE user_id = $1
                ORDER BY click_count DESC, last_viewed DESC
                LIMIT 10
                """
                user_history = await self.db.fetch(user_history_query, uid)
                # Convert DB integers to strings for consistent handling
                user_book_ids = [str(row["book_id"]) for row in user_history] if user_history else []
                print(f"Found {len(user_book_ids)} books in user history")
            except Exception as e:
                print(f"⚠️ Error fetching user history: {e}")
                user_book_ids = []
            
            # Get genres from user's books (using string IDs)
            user_genres = set()
            if user_book_ids:
                try:
                    user_books = await fetch_books_by_ids(user_book_ids[:5])
                    for book in user_books:
                        if book.get("genres"):
                            genres = [g.strip() for g in book["genres"].split(',')]
                            user_genres.update(genres)
                    print(f"Found genres: {user_genres}")
                except Exception as e:
                    print(f"⚠️ Error fetching user books: {e}")
            
            # 2. Find similar users (who viewed same books)
            if user_book_ids:
                try:
                    # Convert string IDs to integers for DB query
                    int_user_book_ids = [int(bid) for bid in user_book_ids if bid]
                    
                    similar_users_query = """
                    SELECT DISTINCT user_id
                    FROM user_book_views
                    WHERE book_id = ANY($1::int[]) AND user_id != $2
                    LIMIT 20
                    """
                    similar_users = await self.db.fetch(similar_users_query, int_user_book_ids, uid)
                    similar_user_ids = [row["user_id"] for row in similar_users] if similar_users else []

                    if similar_user_ids:
                        popular_from_similar_query = """
                        SELECT book_id, SUM(click_count) as total_clicks
                        FROM user_book_views
                        WHERE user_id = ANY($1::int[])
                        AND book_id != ALL($2::int[])
                        GROUP BY book_id
                        ORDER BY total_clicks DESC
                        LIMIT $3
                        """
                        similar_popular = await self.db.fetch(
                            popular_from_similar_query, 
                            similar_user_ids, 
                            int_user_book_ids,
                            books_needed
                        )
                        for row in similar_popular or []:
                            book_id_str = str(row["book_id"])
                            if book_id_str not in recommended_ids:
                                recommended_ids.append(book_id_str)
                        print(f"Found {len(recommended_ids)} books from similar users")
                except Exception as e:
                    print(f"⚠️ Error finding similar users: {e}")
            
            # 3. Get genre-based recommendations
            if user_genres and len(recommended_ids) < books_needed:
                try:
                    genre_query = " ".join(list(user_genres)[:3])
                    similar_books = search_books(query=genre_query, top_k=books_needed * 2)
                    
                    for book in similar_books or []:
                        if (book["book_id"] not in user_book_ids and 
                            book["book_id"] not in recommended_ids and
                            len(recommended_ids) < books_needed):
                            recommended_ids.append(book["book_id"])
                    print(f"Added {len(recommended_ids)} books from genre matching")
                except Exception as e:
                    print(f"⚠️ Error getting genre recommendations: {e}")
            
            # 4. Fill with globally popular books
            if len(recommended_ids) < books_needed:
                try:
                    popular_needed = books_needed - len(recommended_ids)
                    global_popular_query = """
                    SELECT book_id, COUNT(*) as view_count
                    FROM user_book_views 
                    GROUP BY book_id
                    ORDER BY view_count DESC 
                    LIMIT $1
                    """
                    global_popular = await self.db.fetch(global_popular_query, popular_needed * 2)
                    
                    for row in global_popular or []:
                        book_id_str = str(row["book_id"])
                        if (book_id_str not in user_book_ids and 
                            book_id_str not in recommended_ids and
                            len(recommended_ids) < books_needed):
                            recommended_ids.append(book_id_str)
                    print(f"Added {len(recommended_ids)} popular books")
                except Exception as e:
                    print(f"⚠️ Error fetching popular books: {e}")
            
            # 5. Apply pagination
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_ids = recommended_ids[start_idx:end_idx] if recommended_ids else []
            
            # 6. Fallback to random if no recommendations
            if not paginated_ids:
                print("No recommendations found, using random books")
                try:
                    random_query = "SELECT book_id FROM books ORDER BY RANDOM() LIMIT $1"
                    random_books = await self.db.fetch(random_query, limit)
                    paginated_ids = [str(row["book_id"]) for row in random_books] if random_books else []
                except Exception as e:
                    print(f"⚠️ Error fetching random books: {e}")
                    return []
            
            # 7. Fetch full book details (fetch_books_by_ids expects string IDs)
            books = await fetch_books_by_ids(paginated_ids) if paginated_ids else []
            print(f"Returning {len(books)} recommended books")
            return books
            
        except Exception as e:
            print(f"❌ Critical error in recommendations: {str(e)}")
            # Ultimate fallback - return random books
            try:
                random_query = "SELECT book_id FROM books ORDER BY RANDOM() LIMIT $1"
                random_books = await self.db.fetch(random_query, limit)
                random_ids = [str(row["book_id"]) for row in random_books] if random_books else []
                return await fetch_books_by_ids(random_ids) if random_ids else []
            except Exception:
                return []

    async def _user_has_history(self, user_id: int) -> bool:
        """True if this user has at least one book view."""
        try:
            row = await self.db.fetchrow(
                "SELECT 1 FROM user_book_views WHERE user_id = $1 LIMIT 1",
                user_id,
            )
            return row is not None
        except Exception:
            return False

    async def get_recommended_sections(
        self,
        user_id: str,
        for_you_limit: int = 6,
        popular_limit: int = 12,
        genres_limit: int = 6,
        books_per_genre: int = 4,
    ) -> Dict[str, Any]:
        """
        Return structured sections:
        - popular: always filled (global popular or random)
        - for_you: only when user has past experience
        - by_genre: 4 books per genre
        """
        for_you: List[Dict[str, Any]] = []
        popular: List[Dict[str, Any]] = []
        by_genre: List[Dict[str, Any]] = []

        try:
            uid = int(user_id)
        except (TypeError, ValueError):
            uid = None

        # For you section
        if uid is not None and await self._user_has_history(uid):
            for_you = await self.get_combined_recommendations(
                user_id=str(uid), page=1, limit=for_you_limit
            )

        # 1. Collect all IDs for popular and genres
        all_ids_to_fetch = []
        popular_ids = []
        genre_ids_map = {}

        # Popular section
        try:
            popular_rows = await self.db.fetch(
                """
                SELECT book_id, SUM(click_count) AS total
                FROM user_book_views
                GROUP BY book_id
                ORDER BY total DESC
                LIMIT $1
                """,
                popular_limit,
            )
            if popular_rows:
                popular_ids = [str(row["book_id"]) for row in popular_rows]
            else:
                random_rows = await self.db.fetch(
                    "SELECT book_id FROM books ORDER BY RANDOM() LIMIT $1",
                    popular_limit,
                )
                if random_rows:
                    popular_ids = [str(row["book_id"]) for row in random_rows]
        except Exception as e:
            print(f"Error fetching popular IDs: {e}")
            try:
                random_rows = await self.db.fetch(
                    "SELECT book_id FROM books ORDER BY RANDOM() LIMIT $1",
                    popular_limit,
                )
                if random_rows:
                    popular_ids = [str(r["book_id"]) for r in random_rows]
            except Exception as e2:
                print(f"Fallback popular IDs failed: {e2}")

        all_ids_to_fetch.extend(popular_ids)

        # Genre sections
        try:
            rows = await self.db.fetch(
                """
                SELECT book_id, genres FROM books
                WHERE genres IS NOT NULL AND trim(genres) != ''
                LIMIT 2000
                """
            )
            genre_to_all_ids: Dict[str, List[str]] = {}
            for r in rows:
                gs = (r["genres"] or "").strip()
                if not gs:
                    continue
                for g in gs.split(","):
                    g = g.strip()
                    if not g:
                        continue
                    if g not in genre_to_all_ids:
                        genre_to_all_ids[g] = []
                    genre_to_all_ids[g].append(str(r["book_id"]))

            genre_names = list(genre_to_all_ids.keys())[:genres_limit]
            for genre in genre_names:
                ids = genre_to_all_ids[genre]
                chosen = ids if len(ids) <= books_per_genre else random.sample(ids, books_per_genre)
                genre_ids_map[genre] = chosen
                all_ids_to_fetch.extend(chosen)
        except Exception as e:
            print(f"Error gathering genre IDs: {e}")

        # 2. Fetch all books in ONE single call
        unique_ids = list(set(all_ids_to_fetch))
        all_fetched_books = await fetch_books_by_ids(unique_ids)
        book_map = {str(b["book_id"]): b for b in all_fetched_books}

        # 3. Reconstruct popular and by_genre sections from book_map
        popular = [book_map[bid] for bid in popular_ids if bid in book_map]
        
        for genre, ids in genre_ids_map.items():
            books_list = [book_map[bid] for bid in ids if bid in book_map]
            if books_list:
                by_genre.append({"genre": genre, "books": books_list})

        return {
            "for_you": for_you,
            "popular": popular,
            "by_genre": by_genre,
        }