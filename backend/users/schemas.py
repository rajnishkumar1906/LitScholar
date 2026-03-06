from datetime import date , datetime
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    email: str


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    yearly_goal: Optional[int] = None
    monthly_goal: Optional[int] = None
    categories_read: Optional[List[str]] = None


class UserReadingProfile(BaseModel):
    total_books_read: int = 0
    total_pages_read: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    # last_read_date: Optional[date] = None
    yearly_goal: int = 0
    monthly_goal: int = 0
    yearly_progress: int = 0
    monthly_progress: int = 0
    categories_read: List[str] = []


class FinishBookRequest(BaseModel):
    book_id: str


class UserBookResponse(BaseModel):
    id: int
    user_id: int
    book_id: str
    book_title: str
    author: str
    list_type: str
    start_date: Optional[date] = None
    finish_date: Optional[date] = None
    rating: Optional[int] = None
    cover_image_url: Optional[str] = None


class UserActivityResponse(BaseModel):
    activity_type: str
    book_id: str
    book_title: Optional[str] = None
    rating: Optional[int] = None
    list_type: Optional[str] = None
    created_at: datetime
    metadata: Optional[dict] = None