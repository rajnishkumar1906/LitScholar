from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from books.schemas import (
    Book, RecommendedBook, RecommendedSectionsResponse, 
    TrackBookResponse, UserBookCreate, UserBookResponse
)
from books.service import BookService
from core.db import get_async_db
from core.security import get_current_user_with_db
import asyncpg

router = APIRouter()

async def get_book_service(
    db: asyncpg.Connection = Depends(get_async_db),
) -> BookService:
    return BookService(db)

@router.get("/ping")
async def ping():
    return {"message": "pong"}

@router.get("/recommended", response_model=List[RecommendedBook])
async def get_recommended_books(
    page: int = Query(1, ge=1),
    limit: int = Query(8, ge=1, le=50),
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    try:
        books = await service.get_hybrid_recommendations(
            user_id=str(current_user["id"]),
            limit=limit * 2
        )
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        return books[start_idx:end_idx]
        
    except Exception as e:
        print(f"Error in recommendations: {str(e)}")
        return []

@router.get("/recommended/sections", response_model=RecommendedSectionsResponse)
async def get_recommended_sections(
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    try:
        data = await service.get_recommended_sections(
            user_id=str(current_user["id"]),
            for_you_limit=6,
            popular_limit=12,
            genres_limit=6,
            books_per_genre=4,
        )
        return data
    except Exception as e:
        print(f"Error in recommended sections: {e}")
        return RecommendedSectionsResponse(for_you=[], popular=[], by_genre=[])

@router.post("/track/{book_id}", response_model=TrackBookResponse)
async def track_book(
    book_id: str,
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    try:
        result = await service.track_book_view(current_user["id"], book_id)
        return {"success": True, "message": "Book view tracked", "data": result}
    except Exception as e:
        print(f"Error in track_book: {e}")
        return {"success": False, "message": "Failed to track book view"}

@router.post("/user/books", response_model=dict)
async def add_user_book(
    book_data: UserBookCreate,
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
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

@router.get("/{book_id}/summary")
async def get_book_summary(
    book_id: str,
    service: BookService = Depends(get_book_service)
):
    summary = await service.get_book_summary(book_id)
    return {"summary": summary}

@router.get("/{book_id}", response_model=Book)
async def get_book(
    book_id: str,
    service: BookService = Depends(get_book_service)
):
    book = await service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.get("/debug/check-books")
async def check_books(db: asyncpg.Connection = Depends(get_async_db)):
    rows = await db.fetch("SELECT book_id, book_title FROM books LIMIT 10")
    return {"sample_books": [dict(r) for r in rows]}