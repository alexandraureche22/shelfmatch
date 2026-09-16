from sqlalchemy import func, text
from sqlalchemy.orm import Session
from . import models, schemas


def get_or_create_book(db: Session, book: schemas.BookCreate) -> models.Book:
    existing = None
    if book.google_books_id:
        existing = db.query(models.Book).filter(
            models.Book.google_books_id == book.google_books_id
        ).first()
    if existing:
        return existing
    new_book = models.Book(**book.model_dump())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


def create_user_book(db: Session, entry: schemas.UserBookCreate) -> models.UserBook:
    new_entry = models.UserBook(**entry.model_dump())
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


def list_user_books(db: Session, status: str | None = None):
    q = db.query(models.UserBook)
    if status:
        q = q.filter(models.UserBook.status == status)
    return q.all()


def get_genre_stats(db: Session):
    """Citește din view-ul genre_stats definit în schema.sql."""
    result = db.execute(text("SELECT genre, books_finished, avg_rating, avg_pages_per_day FROM genre_stats"))
    return [
        {"genre": r[0], "books_finished": r[1], "avg_rating": r[2], "avg_pages_per_day": r[3]}
        for r in result
    ]


def get_top_genres(db: Session, limit: int = 3):
    """Genurile preferate, ordonate după rating mediu — folosit la recomandări."""
    rows = (
        db.query(
            models.Book.genre,
            func.avg(models.UserBook.rating).label("avg_rating"),
        )
        .join(models.UserBook, models.UserBook.book_id == models.Book.id)
        .filter(models.UserBook.status == "finished", models.UserBook.rating.isnot(None))
        .group_by(models.Book.genre)
        .order_by(func.avg(models.UserBook.rating).desc())
        .limit(limit)
        .all()
    )
    return [r[0] for r in rows if r[0]]


def get_read_google_ids(db: Session) -> set[str]:
    rows = db.query(models.Book.google_books_id).filter(models.Book.google_books_id.isnot(None)).all()
    return {r[0] for r in rows}
