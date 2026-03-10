from pydantic import BaseModel
from typing import List


class AssistantRequest(BaseModel):
    question: str
    top_k: int = 5


class BookResponse(BaseModel):
    book_id: str
    title: str
    author: str
    genres: str | None = None
    image_url: str | None = None


class AssistantResponse(BaseModel):
    question: str
    answer: str
    books: List[BookResponse]