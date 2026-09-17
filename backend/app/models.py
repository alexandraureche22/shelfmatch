import enum
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, SmallInteger, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from .database import Base


class ReadingStatus(str, enum.Enum):
    wishlist = "wishlist"
    reading = "reading"
    finished = "finished"


class FriendshipStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"


class ChallengeVisibility(str, enum.Enum):
    public = "public"
    friends = "friends"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    books = relationship("UserBook", back_populates="user")


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
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    rating = Column(SmallInteger)
    date_started = Column(Date)
    date_finished = Column(Date)
    status = Column(Enum(ReadingStatus, name="reading_status"), nullable=False, default=ReadingStatus.wishlist)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="books")
    book = relationship("Book", back_populates="user_entries")

class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    addressee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(FriendshipStatus, name="friendship_status"), nullable=False, default=FriendshipStatus.pending)
    created_at = Column(DateTime, server_default=func.now())

    requester = relationship("User", foreign_keys=[requester_id])
    addressee = relationship("User", foreign_keys=[addressee_id])


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # NULL = oficial
    title = Column(String(255), nullable=False)
    description = Column(Text)
    month = Column(String(7), nullable=False)  # 'YYYY-MM'
    visibility = Column(Enum(ChallengeVisibility, name="challenge_visibility"), nullable=False, default=ChallengeVisibility.friends)
    created_at = Column(DateTime, server_default=func.now())

    creator = relationship("User", foreign_keys=[creator_id])
class ChallengeCompletion(Base):
    __tablename__ = "challenge_completions"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_book_id = Column(Integer, ForeignKey("user_books.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    challenge = relationship("Challenge")
    user = relationship("User")
    user_book = relationship("UserBook")