from pydantic import BaseModel
from typing import Optional, List

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