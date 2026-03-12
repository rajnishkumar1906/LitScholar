from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date, datetime

# ============ BASE BOOK SCHEMAS ============

class Book(BaseModel):
    book_id: str
    title: str
    author: str
    genres: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    num_pages: Optional[int] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class RecommendedBook(BaseModel):
    book_id: str
    title: str
    author: str
    genres: Optional[str] = None
    summary: Optional[str] = None
    num_pages: Optional[int] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

# ============ RECOMMENDATION SECTION SCHEMAS ============

class GenreSection(BaseModel):
    """A single genre section with its books"""
    genre: str
    books: List[RecommendedBook]

class RecommendedSectionsResponse(BaseModel):
    """Complete response for all recommendation sections"""
    for_you: List[RecommendedBook]
    popular: List[RecommendedBook]
    by_genre: List[GenreSection]

# ============ PAGINATION SCHEMAS ============

class PaginatedResponse(BaseModel):
    """Paginated response with hasMore flag"""
    books: List[RecommendedBook]
    hasMore: bool
    page: int
    total: Optional[int] = None
    success: bool = True
    error: Optional[str] = None

# ============ TRACKING SCHEMAS ============

class TrackBookResponse(BaseModel):
    """Response for tracking book views"""
    success: bool
    message: str
    data: Optional[dict] = None

# ============ USER BOOK SCHEMAS ============

class UserBookCreate(BaseModel):
    """Request body for adding a book to user's list"""
    book_id: str
    list_type: str  # 'wishlist', 'reading', 'finished'
    rating: Optional[int] = None
    notes: Optional[str] = None

class UserBookResponse(BaseModel):
    """Response for user's book list items"""
    id: int
    user_id: int
    book_id: str
    list_type: str
    start_date: Optional[date] = None
    finish_date: Optional[date] = None
    rating: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True