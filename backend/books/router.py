from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from books.schemas import Book, RecommendedBook, RecommendedSectionsResponse
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
    limit: int = Query(6, ge=1, le=50),
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    try:
        books = await service.get_combined_recommendations(
            user_id=current_user["id"],
            page=page,
            limit=limit,
        )
        return books
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
        return RecommendedSectionsResponse(**data)
    except Exception as e:
        print(f"Error in recommended sections: {e}")
        return RecommendedSectionsResponse(for_you=[], popular=[], by_genre=[])

@router.post("/track/{book_id}")
async def track_book(
    book_id: str,
    current_user: dict = Depends(get_current_user_with_db),
    service: BookService = Depends(get_book_service),
):
    try:
        result = await service.track_book_view(current_user["id"], book_id)
        return {"success": True, "message": "Book view tracked", "data": result}
    except Exception as e:
        # Tracking failures should not break the main user flow.
        print(f"Error in track_book: {e}")
        return {"success": False, "message": "Failed to track book view"}

@router.get("/{book_id}", response_model=Book)
async def get_book(
    book_id: str,
    service: BookService = Depends(get_book_service)
):
    book = await service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.get("/{book_id}/summary")
async def get_book_summary(
    book_id: str,
    service: BookService = Depends(get_book_service)
):
    summary = await service.get_book_summary(book_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not available")
    return {"summary": summary}

# Add this temporary endpoint to check
@router.get("/debug/check-books")
async def check_books(db: asyncpg.Connection = Depends(get_async_db)):
    # Get first 10 books from database
    rows = await db.fetch("SELECT book_id, book_title FROM books LIMIT 10")
    return {"sample_books": [dict(r) for r in rows]}