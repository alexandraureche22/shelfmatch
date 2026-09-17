from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
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


class UserBookUpdate(BaseModel):
    """Toate câmpurile opționale — trimiți doar ce vrei să schimbi."""
    rating: Optional[int] = None
    date_started: Optional[date] = None
    date_finished: Optional[date] = None
    status: Optional[ReadingStatus] = None


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


# ---------- Auth ----------

class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# ---------- Friends ----------

class FriendRequestCreate(BaseModel):
    email: EmailStr


class FriendOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str


class FriendRequestOut(BaseModel):
    id: int
    requester: FriendOut


# ---------- Feed ----------

class FeedItemOut(BaseModel):
    user_email: str
    book_title: str
    book_author: Optional[str]
    cover_url: Optional[str]
    status: ReadingStatus
    rating: Optional[int]
    date: Optional[date]


# ---------- Challenges ----------

class ChallengeCreate(BaseModel):
    title: str
    description: Optional[str] = None
    month: str  # 'YYYY-MM'


class ChallengeOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    month: str
    visibility: str
    creator_email: Optional[str] = None

class ChallengeCompleteCreate(BaseModel):
    user_book_id: int


class ChallengeCompletionOut(BaseModel):
    user_email: str
    book_title: str
    cover_url: Optional[str] = None