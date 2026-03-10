from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class Book(BaseModel):
    book_id: str
    title: str
    author: str
    genres: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    num_pages: Optional[int] = None
    image_url: Optional[str] = None

class RecommendedBook(BaseModel):
    book_id: str
    title: str
    author: str
    genres: Optional[str] = None
    summary: Optional[str] = None
    num_pages: Optional[int] = None
    image_url: Optional[str] = None

class GenreSection(BaseModel):
    genre: str
    books: List[RecommendedBook]

class RecommendedSectionsResponse(BaseModel):
    for_you: List[RecommendedBook]
    popular: List[RecommendedBook]
    by_genre: List[GenreSection]

class TrackBookResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class UserBookCreate(BaseModel):
    book_id: str
    list_type: str  # 'wishlist', 'reading', 'finished'
    rating: Optional[int] = None
    notes: Optional[str] = None

class UserBookResponse(BaseModel):
    id: int
    user_id: int
    book_id: str
    list_type: str
    start_date: Optional[date] = None
    finish_date: Optional[date] = None
    rating: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime