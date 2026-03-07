import asyncpg
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

class UserService:
    def __init__(self, db: asyncpg.Connection):
        self.db = db
    
    async def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Get user details by ID"""
        row = await self.db.fetchrow(
            """
            SELECT id, email, full_name, bio, location, created_at
            FROM users 
            WHERE id = $1
            """,
            user_id
        )
        return dict(row) if row else {}
    
    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get user's reading profile"""
        row = await self.db.fetchrow(
            """
            SELECT
                total_books_read,
                total_pages_read,
                current_streak,
                longest_streak,
                last_read_date,
                yearly_goal,
                monthly_goal,
                yearly_progress,
                monthly_progress,
                categories_read
            FROM user_reading_profile
            WHERE user_id = $1
            """,
            user_id
        )
        return dict(row) if row else {}
    
    async def update_user_info(self, user_id: int, full_name: Optional[str] = None, 
                               bio: Optional[str] = None, location: Optional[str] = None) -> None:
        """Update user basic info"""
        updates = []
        params = []
        param_index = 1
        
        if full_name is not None:
            updates.append(f"full_name = ${param_index}")
            params.append(full_name)
            param_index += 1
        
        if bio is not None:
            updates.append(f"bio = ${param_index}")
            params.append(bio)
            param_index += 1
            
        if location is not None:
            updates.append(f"location = ${param_index}")
            params.append(location)
            param_index += 1
        
        if updates:
            query = f"UPDATE users SET {', '.join(updates)}, updated_at = NOW() WHERE id = ${param_index}"
            params.append(user_id)
            await self.db.execute(query, *params)
    
    async def update_reading_profile(self, user_id: int, yearly_goal: Optional[int] = None,
                                    monthly_goal: Optional[int] = None, 
                                    categories_read: Optional[List[str]] = None) -> None:
        """Update user's reading profile"""
        exists = await self.db.fetchval(
            "SELECT EXISTS(SELECT 1 FROM user_reading_profile WHERE user_id = $1)",
            user_id
        )
        
        if exists:
            updates = []
            params = []
            param_index = 1
            
            if yearly_goal is not None:
                updates.append(f"yearly_goal = ${param_index}")
                params.append(yearly_goal)
                param_index += 1
            
            if monthly_goal is not None:
                updates.append(f"monthly_goal = ${param_index}")
                params.append(monthly_goal)
                param_index += 1
            
            if categories_read is not None:
                updates.append(f"categories_read = ${param_index}")
                params.append(json.dumps(categories_read))
                param_index += 1
            
            if updates:
                query = f"UPDATE user_reading_profile SET {', '.join(updates)}, updated_at = NOW() WHERE user_id = ${param_index}"
                params.append(user_id)
                await self.db.execute(query, *params)
        else:
            await self.db.execute("""
                INSERT INTO user_reading_profile 
                (user_id, yearly_goal, monthly_goal, categories_read, updated_at)
                VALUES ($1, $2, $3, $4, NOW())
            """, 
                user_id,
                yearly_goal or 0,
                monthly_goal or 0,
                json.dumps(categories_read or [])
            )
    
    async def get_user_books(self, user_id: int, list_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get user's books with optional filtering"""
        query = """
            SELECT 
                ub.*,
                b.book_title,
                b.author,
                b.cover_image_url
            FROM user_books ub
            JOIN books b ON ub.book_id = b.book_id
            WHERE ub.user_id = $1
        """
        params = [user_id]
        param_index = 2
        
        if list_type:
            query += f" AND ub.list_type = ${param_index}"
            params.append(list_type)
            param_index += 1
        
        query += f" ORDER BY ub.finish_date DESC NULLS LAST, ub.created_at DESC LIMIT ${param_index}"
        params.append(limit)
        
        rows = await self.db.fetch(query, *params)
        return [dict(row) for row in rows]
    
    async def get_user_activity(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's recent activity"""
        query = """
            SELECT 
                activity_type,
                book_id,
                rating,
                list_type,
                created_at,
                metadata,
                b.book_title
            FROM (
                (SELECT 
                    'book_view' as activity_type,
                    book_id::bigint as book_id,
                    NULL::int as rating,
                    NULL::text as list_type,
                    last_viewed as created_at,
                    jsonb_build_object('click_count', click_count) as metadata
                FROM user_book_views
                WHERE user_id = $1)
                
                UNION ALL
                
                (SELECT 
                    CASE 
                        WHEN list_type = 'finished' THEN 'finished_book'
                        WHEN list_type = 'reading' THEN 'started_book'
                        ELSE 'added_to_' || COALESCE(list_type, 'list')
                    END as activity_type,
                    book_id::bigint as book_id,
                    rating::int as rating,
                    list_type::text as list_type,
                    COALESCE(finish_date, start_date, created_at) as created_at,
                    jsonb_build_object(
                        'list_type', list_type,
                        'rating', rating
                    ) as metadata
                FROM user_books
                WHERE user_id = $1)
            ) AS combined_activity
            LEFT JOIN books b ON b.book_id = combined_activity.book_id
            ORDER BY created_at DESC
            LIMIT $2
        """
        
        try:
            rows = await self.db.fetch(query, user_id, limit)
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error in get_user_activity: {e}")
            return []
    
    async def mark_book_as_finished(self, user_id: int, book_id: str) -> Dict[str, Any]:
        """Mark a book as finished and update reading progress"""
        # Check if book exists
        book_exists = await self.db.fetchval(
            "SELECT EXISTS(SELECT 1 FROM books WHERE book_id = $1)",
            book_id
        )
        if not book_exists:
            raise ValueError("Book not found")
        
        # Add to user_books as finished
        await self.db.execute("""
            INSERT INTO user_books (user_id, book_id, list_type, finish_date)
            VALUES ($1, $2, 'finished', NOW())
            ON CONFLICT (user_id, book_id, list_type) 
            DO UPDATE SET finish_date = NOW(), updated_at = NOW()
        """, user_id, book_id)
        
        # Get book pages
        pages = await self.db.fetchval(
            "SELECT num_pages FROM books WHERE book_id = $1",
            book_id
        ) or 0
        
        # Update or create reading profile
        profile_exists = await self.db.fetchval(
            "SELECT EXISTS(SELECT 1 FROM user_reading_profile WHERE user_id = $1)",
            user_id
        )
        
        if profile_exists:
            # Get current streak info
            last_read = await self.db.fetchval(
                "SELECT last_read_date FROM user_reading_profile WHERE user_id = $1",
                user_id
            )
            
            # Increment counters
            await self.db.execute("""
                UPDATE user_reading_profile 
                SET total_books_read = total_books_read + 1,
                    total_pages_read = total_pages_read + $2,
                    last_read_date = CURRENT_DATE,
                    updated_at = NOW()
                WHERE user_id = $1
            """, user_id, pages)
            
            # Update streak logic
            if last_read:
                await self.db.execute("""
                    UPDATE user_reading_profile 
                    SET current_streak = CASE 
                        WHEN last_read_date = CURRENT_DATE - INTERVAL '1 day' THEN current_streak + 1
                        WHEN last_read_date = CURRENT_DATE THEN current_streak
                        ELSE 1
                    END,
                    longest_streak = GREATEST(longest_streak, 
                        CASE 
                            WHEN last_read_date = CURRENT_DATE - INTERVAL '1 day' THEN current_streak + 1
                            WHEN last_read_date = CURRENT_DATE THEN current_streak
                            ELSE 1
                        END
                    )
                    WHERE user_id = $1
                """, user_id)
        else:
            # Create new profile
            await self.db.execute("""
                INSERT INTO user_reading_profile 
                (user_id, total_books_read, total_pages_read, last_read_date, current_streak, longest_streak)
                VALUES ($1, 1, $2, CURRENT_DATE, 1, 1)
            """, user_id, pages)
        
        # Add activity
        await self.db.execute("""
            INSERT INTO user_activity (user_id, activity_type, book_id, metadata, created_at)
            VALUES ($1, $2, $3, $4, NOW())
        """, user_id, 'finished_book', book_id, json.dumps({
            'action': 'finished',
            'timestamp': str(datetime.now())
        }))
        
        return {"success": True, "message": "Book marked as finished!"}