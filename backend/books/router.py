from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import asyncpg

from books.schemas import (
    Book,
    RecommendedBook,
    RecommendedSectionsResponse,
    TrackBookResponse,
    UserBookCreate,
    UserBookResponse,
    PaginatedResponse,
    FinishBookRequest,
)
from books.service import BookService
from core.db import get_async_db
from core.security import get_current_user_with_db

router = APIRouter()

async def get_book_service(
    db: asyncpg.Connection = Depends(get_async_db),
) -> BookService:
    return BookService(db)

@router.get("/ping")
async def ping():
    return {"message": "pong"}

# ============ BASIC BOOK ENDPOINTS ============

@router.get("/{book_id}", response_model=Book)
async def get_book(
    book_id: str,
    service: BookService = Depends(get_book_service)
):
    """Get a single book by ID"""
    book = await service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.get("/{book_id}/summary")
async def get_book_summary(
    book_id: str,
    service: BookService = Depends(get_book_service)
):
    """Get or generate book summary"""
    summary = await service.get_book_summary(book_id)
    return {"summary": summary}

# ============ 4 CORE RECOMMENDATION ENDPOINTS ============

@router.get("/recommended/for-you")
async def get_for_you_recommendations(
    limit: int = Query(8, ge=1, le=20),
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    """
    Get personalized 'For You' recommendations
    Uses content-based similarity from user's viewed books
    """
    try:
        books = await service.get_for_you_recommendations(
            user_id=str(current_user["id"]),
            limit=limit
        )
        return {"books": books, "success": True}
    except Exception as e:
        print(f"❌ Error in for-you recommendations: {e}")
        return {"books": [], "success": False, "error": str(e)}

@router.get("/recommended/popular")
async def get_popular_recommendations(
    limit: int = Query(8, ge=1, le=20),
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    """
    Get popular/trending books
    Based on user views and interactions
    """
    try:
        books = await service.get_popular_recommendations(
            limit=limit
        )
        return {"books": books, "success": True}
    except Exception as e:
        print(f"❌ Error in popular recommendations: {e}")
        return {"books": [], "success": False, "error": str(e)}

@router.get("/recommended/by-genre")
async def get_genre_recommendations(
    limit: int = Query(4, ge=1, le=10),
    books_per_genre: int = Query(4, ge=1, le=8),
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    """
    Get books grouped by genre
    Returns array of { genre: string, books: [] }
    """
    try:
        genre_sections = await service.get_genre_recommendations(
            genres_limit=limit,
            books_per_genre=books_per_genre
        )
        return {"books": genre_sections, "success": True}
    except Exception as e:
        print(f"❌ Error in genre recommendations: {e}")
        return {"books": [], "success": False, "error": str(e)}

@router.get("/recommended/similar", response_model=PaginatedResponse)
async def get_similar_recommendations(
    page: int = Query(1, ge=1),
    limit: int = Query(8, ge=1, le=20),
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    """
    Get similar book recommendations with pagination
    Uses retrieval-based similarity from user's recent book
    """
    try:
        # Fetch one extra to determine if there are more pages
        books = await service.get_similar_recommendations(
            user_id=str(current_user["id"]),
            page=page,
            limit=limit + 1  # Fetch one extra for hasMore logic
        )
        
        # Check if we have more pages
        has_more = len(books) > limit
        
        # Return only the requested number of books
        result_books = books[:limit]
        
        return {
            "books": result_books,
            "hasMore": has_more,
            "page": page,
            "total": len(result_books),
            "success": True
        }
    except Exception as e:
        print(f"❌ Error in similar recommendations: {e}")
        return {
            "books": [],
            "hasMore": False,
            "page": page,
            "success": False,
            "error": str(e)
        }

# ============ ADDITIONAL ENDPOINTS ============

@router.get("/recommended/sections", response_model=RecommendedSectionsResponse)
async def get_all_recommendation_sections(
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    """
    Get all recommendation sections at once
    Returns for_you, popular, and by_genre sections
    """
    try:
        data = await service.get_all_recommendation_sections(
            user_id=str(current_user["id"])
        )
        return data
    except Exception as e:
        print(f"Error in recommendation sections: {e}")
        return RecommendedSectionsResponse(
            for_you=[], 
            popular=[], 
            by_genre=[]
        )

# ============ USER BOOK INTERACTIONS ============

@router.post("/track/{book_id}", response_model=TrackBookResponse)
async def track_book_view(
    book_id: str,
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    """Track user book view"""
    try:
        result = await service.track_book_view(current_user["id"], book_id)
        return {"success": True, "message": "Book view tracked", "data": result}
    except Exception as e:
        print(f"Error in track_book: {e}")
        return {"success": False, "message": "Failed to track book view"}

@router.post("/user/books", response_model=dict)
async def add_to_user_books(
    book_data: UserBookCreate,
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    """Add book to user's list (wishlist, reading, finished)"""
    try:
        result = await service.add_user_book(
            user_id=str(current_user["id"]),
            book_id=book_data.book_id,
            list_type=book_data.list_type,
            rating=book_data.rating,
            notes=book_data.notes
        )
        return result
    except Exception as e:
        print(f"Error adding user book: {e}")
        return {"success": False, "message": str(e)}

@router.get("/user/books", response_model=List[UserBookResponse])
async def get_user_books(
    list_type: Optional[str] = Query(None, regex="^(wishlist|reading|finished)$"),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    """Get user's books by list type"""
    try:
        books = await service.get_user_books(
            user_id=str(current_user["id"]),
            list_type=list_type,
            limit=limit
        )
        return books
    except Exception as e:
        print(f"Error getting user books: {e}")
        return []


@router.post("/finish")
async def mark_book_finished(
    payload: FinishBookRequest,
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    """
    Mark a book as finished for the current user.
    Idempotent: if it's already in the finished list, returns success.
    """
    try:
      result = await service.add_user_book(
          user_id=str(current_user["id"]),
          book_id=payload.book_id,
          list_type="finished",
          rating=None,
          notes=None,
      )

      # Treat "already finished" as success so the button doesn't error
      if not result.get("success") and "already in finished" in result.get("message", "").lower():
          return {"success": True, "message": "Book already marked as finished"}

      return result
    except Exception as e:
      print(f"Error marking book as finished: {e}")
      return {"success": False, "message": str(e)}

# ============ DEBUG ENDPOINTS ============

@router.get("/debug/check-books")
async def debug_check_books(db: asyncpg.Connection = Depends(get_async_db)):
    """Debug endpoint to check books in database"""
    rows = await db.fetch("SELECT book_id, book_title FROM books LIMIT 10")
    return {"sample_books": [dict(r) for r in rows]}

@router.get("/debug/stats")
async def debug_database_stats(db: asyncpg.Connection = Depends(get_async_db)):
    """Get database statistics"""
    try:
        total_books = await db.fetchval("SELECT COUNT(*) FROM books")
        books_with_views = await db.fetchval("SELECT COUNT(DISTINCT book_id) FROM user_book_views")
        total_users = await db.fetchval("SELECT COUNT(*) FROM users")
        
        return {
            "total_books": total_books,
            "books_with_views": books_with_views,
            "total_users": total_users,
            "can_paginate": books_with_views >= 8
        }
    except Exception as e:
        return {"error": str(e)}