from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from .models import ReadingStatus


class BookBase(BaseModel):
    title: str
    author: Optional[str] = None
    genre: Optional[str] = None
    pages: Optional[int] = None
    google_books_id: Optional[str] = None
    cover_url: Optional[str] = None


class BookCreate(BookBase):
    pass


class BookOut(BookBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class UserBookCreate(BaseModel):
    book_id: int
    rating: Optional[int] = None
    date_started: Optional[date] = None
    date_finished: Optional[date] = None
    status: ReadingStatus = ReadingStatus.wishlist


class UserBookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    book_id: int
    rating: Optional[int]
    date_started: Optional[date]
    date_finished: Optional[date]
    status: ReadingStatus
    book: BookOut


class GenreStatOut(BaseModel):
    genre: str
    books_finished: int
    avg_rating: Optional[float]
    avg_pages_per_day: Optional[float]


class RecommendationOut(BaseModel):
    title: str
    author: Optional[str]
    genre: Optional[str]
    pages: Optional[int]
    google_books_id: Optional[str]
    cover_url: Optional[str]
    estimated_days_to_read: Optional[float] = None
