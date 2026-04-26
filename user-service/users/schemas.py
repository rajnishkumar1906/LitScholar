from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
import json


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
    last_read_date: Optional[date] = None
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
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        """Parse metadata if it's a string"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return {}
        return v or {}


class QuizScoreRequest(BaseModel):
    book_id: str
    book_title: str
    score: int
    total_questions: int = 5
    quiz_results: Optional[List[Dict[str, Any]]] = None


class QuizScoreResponse(BaseModel):
    id: int
    user_id: int
    book_id: str
    book_title: str
    score: int
    total_questions: int
    quiz_results: Optional[List[Dict[str, Any]]] = None
    created_at: datetime