import enum
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, SmallInteger, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from .database import Base


class ReadingStatus(str, enum.Enum):
    wishlist = "wishlist"
    reading = "reading"
    finished = "finished"


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255))
    genre = Column(String(100))
    pages = Column(Integer)
    google_books_id = Column(String(50), unique=True)
    cover_url = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    user_entries = relationship("UserBook", back_populates="book")


class UserBook(Base):
    __tablename__ = "user_books"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    rating = Column(SmallInteger)
    date_started = Column(Date)
    date_finished = Column(Date)
    status = Column(Enum(ReadingStatus, name="reading_status"), nullable=False, default=ReadingStatus.wishlist)
    created_at = Column(DateTime, server_default=func.now())

    book = relationship("Book", back_populates="user_entries")
