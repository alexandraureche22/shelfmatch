from sqlalchemy import func
from sqlalchemy.orm import Session
from . import models, schemas


# ---------- Users ----------

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, email: str, password_hash: str) -> models.User:
    user = models.User(email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------- Books (catalog, nu e legat de user) ----------

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


# ---------- User books (istoricul personal, mereu filtrat pe user_id) ----------

def create_user_book(db: Session, user_id: int, entry: schemas.UserBookCreate) -> models.UserBook:
    new_entry = models.UserBook(user_id=user_id, **entry.model_dump())
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


def list_user_books(db: Session, user_id: int, status: str | None = None):
    q = db.query(models.UserBook).filter(models.UserBook.user_id == user_id)
    if status:
        q = q.filter(models.UserBook.status == status)
    return q.order_by(models.UserBook.created_at.desc()).all()


def get_user_book(db: Session, user_id: int, entry_id: int) -> models.UserBook | None:
    return db.query(models.UserBook).filter(
        models.UserBook.id == entry_id,
        models.UserBook.user_id == user_id,
    ).first()


def update_user_book(db: Session, user_id: int, entry_id: int, updates: schemas.UserBookUpdate) -> models.UserBook | None:
    entry = get_user_book(db, user_id, entry_id)
    if not entry:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


def delete_user_book(db: Session, user_id: int, entry_id: int) -> bool:
    entry = get_user_book(db, user_id, entry_id)
    if not entry:
        return False
    db.delete(entry)
    db.commit()
    return True


def get_genre_stats(db: Session, user_id: int):
    """Statistici per-gen, pentru cărțile terminate de user-ul curent.
    Ritmul (pagini/zi) apare doar dacă ai completat ambele date; rating-ul apare oricum."""
    from sqlalchemy import case

    pace_expr = case(
        (
            (models.UserBook.date_started.isnot(None)) & (models.UserBook.date_finished.isnot(None)),
            models.Book.pages / func.nullif(
                models.UserBook.date_finished - models.UserBook.date_started, 0
            ),
        ),
        else_=None,
    )

    rows = (
        db.query(
            models.Book.genre,
            func.count(models.UserBook.id).label("books_finished"),
            func.avg(models.UserBook.rating).label("avg_rating"),
            func.avg(pace_expr).label("avg_pages_per_day"),
        )
        .join(models.Book, models.Book.id == models.UserBook.book_id)
        .filter(
            models.UserBook.user_id == user_id,
            models.UserBook.status == "finished",
        )
        .group_by(models.Book.genre)
        .all()
    )
    return [
        {
            "genre": r.genre,
            "books_finished": r.books_finished,
            "avg_rating": round(float(r.avg_rating), 2) if r.avg_rating else None,
            "avg_pages_per_day": round(float(r.avg_pages_per_day), 2) if r.avg_pages_per_day else None,
        }
        for r in rows
    ]


def get_top_genres(db: Session, user_id: int, limit: int = 3):
    """Genurile preferate ale user-ului curent, ordonate după rating mediu — pt recomandări."""
    rows = (
        db.query(
            models.Book.genre,
            func.avg(models.UserBook.rating).label("avg_rating"),
        )
        .join(models.UserBook, models.UserBook.book_id == models.Book.id)
        .filter(
            models.UserBook.user_id == user_id,
            models.UserBook.status == "finished",
            models.UserBook.rating.isnot(None),
        )
        .group_by(models.Book.genre)
        .order_by(func.avg(models.UserBook.rating).desc())
        .limit(limit)
        .all()
    )
    return [r[0] for r in rows if r[0]]


def get_read_google_ids(db: Session, user_id: int) -> set[str]:
    rows = (
        db.query(models.Book.google_books_id)
        .join(models.UserBook, models.UserBook.book_id == models.Book.id)
        .filter(models.UserBook.user_id == user_id, models.Book.google_books_id.isnot(None))
        .all()
    )
    return {r[0] for r in rows}

# ---------- Prieteni ----------

def send_friend_request(db: Session, requester_id: int, addressee_email: str):
    addressee = get_user_by_email(db, addressee_email)
    if not addressee:
        return None, "No account with this email."
    if addressee.id == requester_id:
        return None, "You can't add yourself as a friend."

    existing = db.query(models.Friendship).filter(
        ((models.Friendship.requester_id == requester_id) & (models.Friendship.addressee_id == addressee.id)) |
        ((models.Friendship.requester_id == addressee.id) & (models.Friendship.addressee_id == requester_id))
    ).first()
    if existing:
        return None, "A friend request already exists between you two."

    friendship = models.Friendship(requester_id=requester_id, addressee_id=addressee.id, status="pending")
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    return friendship, None


def accept_friend_request(db: Session, user_id: int, request_id: int) -> bool:
    friendship = db.query(models.Friendship).filter(
        models.Friendship.id == request_id,
        models.Friendship.addressee_id == user_id,
        models.Friendship.status == "pending",
    ).first()
    if not friendship:
        return False
    friendship.status = "accepted"
    db.commit()
    return True


def list_pending_requests(db: Session, user_id: int):
    return db.query(models.Friendship).filter(
        models.Friendship.addressee_id == user_id,
        models.Friendship.status == "pending",
    ).all()


def list_friends(db: Session, user_id: int) -> list[models.User]:
    rows = db.query(models.Friendship).filter(
        models.Friendship.status == "accepted",
        (models.Friendship.requester_id == user_id) | (models.Friendship.addressee_id == user_id),
    ).all()
    friend_ids = [
        (r.addressee_id if r.requester_id == user_id else r.requester_id)
        for r in rows
    ]
    if not friend_ids:
        return []
    return db.query(models.User).filter(models.User.id.in_(friend_ids)).all()


def get_friend_ids(db: Session, user_id: int) -> set[int]:
    return {u.id for u in list_friends(db, user_id)}

def remove_friend(db: Session, user_id: int, friend_id: int) -> bool:
    friendship = db.query(models.Friendship).filter(
        models.Friendship.status == "accepted",
        ((models.Friendship.requester_id == user_id) & (models.Friendship.addressee_id == friend_id)) |
        ((models.Friendship.requester_id == friend_id) & (models.Friendship.addressee_id == user_id)),
    ).first()
    if not friendship:
        return False
    db.delete(friendship)
    db.commit()
    return True

# ---------- Feed ----------

def get_feed(db: Session, user_id: int, limit: int = 30):
    friend_ids = get_friend_ids(db, user_id)
    if not friend_ids:
        return []

    rows = (
        db.query(models.UserBook, models.Book, models.User)
        .join(models.Book, models.Book.id == models.UserBook.book_id)
        .join(models.User, models.User.id == models.UserBook.user_id)
        .filter(models.UserBook.user_id.in_(friend_ids), models.UserBook.status != "wishlist")
        .order_by(models.UserBook.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "user_book_id": entry.id,
            "user_email": user.email,
            "book_title": book.title,
            "book_author": book.author,
            "cover_url": book.cover_url,
            "status": entry.status,
            "rating": entry.rating,
            "date": entry.date_finished or entry.date_started,
        }
        for entry, book, user in rows
    ]

# ---------- Reacții pe feed ----------

def can_interact_with_user_book(db: Session, current_user_id: int, user_book_id: int) -> bool:
    """Poți da like/comment doar pe cărțile tale sau ale prietenilor tăi."""
    entry = db.query(models.UserBook).filter(models.UserBook.id == user_book_id).first()
    if not entry:
        return False
    if entry.user_id == current_user_id:
        return True
    return entry.user_id in get_friend_ids(db, current_user_id)


def get_like_info(db: Session, user_id: int, user_book_id: int):
    count = db.query(func.count(models.FeedLike.id)).filter(
        models.FeedLike.user_book_id == user_book_id
    ).scalar() or 0
    liked = db.query(models.FeedLike).filter(
        models.FeedLike.user_book_id == user_book_id, models.FeedLike.user_id == user_id
    ).first() is not None
    return liked, count


def toggle_like(db: Session, user_id: int, user_book_id: int):
    existing = db.query(models.FeedLike).filter(
        models.FeedLike.user_book_id == user_book_id, models.FeedLike.user_id == user_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
    else:
        db.add(models.FeedLike(user_book_id=user_book_id, user_id=user_id))
        db.commit()
    return get_like_info(db, user_id, user_book_id)


def list_comments(db: Session, user_book_id: int):
    rows = (
        db.query(models.FeedComment, models.User)
        .join(models.User, models.User.id == models.FeedComment.user_id)
        .filter(models.FeedComment.user_book_id == user_book_id)
        .order_by(models.FeedComment.created_at.asc())
        .all()
    )
    return [{"user_email": u.email, "text": c.text} for c, u in rows]


def add_comment(db: Session, user_id: int, user_book_id: int, text: str):
    comment = models.FeedComment(user_book_id=user_book_id, user_id=user_id, text=text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


# ---------- Challenges ----------

def create_challenge(db: Session, creator_id: int, payload: schemas.ChallengeCreate) -> models.Challenge:
    challenge = models.Challenge(
        creator_id=creator_id,
        title=payload.title,
        description=payload.description,
        month=payload.month,
        visibility="friends",
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


def list_challenges(db: Session, user_id: int):
    friend_ids = get_friend_ids(db, user_id)
    visible_creator_ids = friend_ids | {user_id}

    rows = (
        db.query(models.Challenge, models.User)
        .outerjoin(models.User, models.User.id == models.Challenge.creator_id)
        .filter(
            (models.Challenge.visibility == "public") |
            (models.Challenge.creator_id.in_(visible_creator_ids))
        )
        .order_by(models.Challenge.month.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "month": c.month,
            "visibility": c.visibility,
            "creator_email": user.email if user else None,
        }
        for c, user in rows
    ]
def complete_challenge(db: Session, user_id: int, challenge_id: int, user_book_id: int):
    """Marchează un challenge ca terminat, folosind o carte din biblioteca ta.
    Dacă mai încercai o dată, actualizează cartea aleasă (upsert)."""
    owned_book = get_user_book(db, user_id, user_book_id)
    if not owned_book:
        return None, "That book isn't in your library."

    existing = db.query(models.ChallengeCompletion).filter(
        models.ChallengeCompletion.challenge_id == challenge_id,
        models.ChallengeCompletion.user_id == user_id,
    ).first()

    if existing:
        existing.user_book_id = user_book_id
        db.commit()
        db.refresh(existing)
        return existing, None

    completion = models.ChallengeCompletion(
        challenge_id=challenge_id, user_id=user_id, user_book_id=user_book_id
    )
    db.add(completion)
    db.commit()
    db.refresh(completion)
    return completion, None


def get_challenge_completions(db: Session, user_id: int, challenge_id: int):
    """Completările vizibile ție pentru un challenge: ale tale + ale prietenilor tăi."""
    visible_ids = get_friend_ids(db, user_id) | {user_id}

    rows = (
        db.query(models.ChallengeCompletion, models.UserBook, models.Book, models.User)
        .join(models.UserBook, models.UserBook.id == models.ChallengeCompletion.user_book_id)
        .join(models.Book, models.Book.id == models.UserBook.book_id)
        .join(models.User, models.User.id == models.ChallengeCompletion.user_id)
        .filter(
            models.ChallengeCompletion.challenge_id == challenge_id,
            models.ChallengeCompletion.user_id.in_(visible_ids),
        )
        .all()
    )
    return [
        {"user_email": user.email, "book_title": book.title, "cover_url": book.cover_url}
        for _, _, book, user in rows
    ]

# ---------- Reading goal ----------

def set_reading_goal(db: Session, user_id: int, year: int, target: int) -> models.ReadingGoal:
    existing = db.query(models.ReadingGoal).filter(
        models.ReadingGoal.user_id == user_id,
        models.ReadingGoal.year == year,
    ).first()
    if existing:
        existing.target = target
        db.commit()
        db.refresh(existing)
        return existing

    goal = models.ReadingGoal(user_id=user_id, year=year, target=target)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_reading_goal(db: Session, user_id: int, year: int):
    """Întoarce (target, câte cărți terminate anul respectiv). target e 0 dacă nu ai setat un obiectiv."""
    goal = db.query(models.ReadingGoal).filter(
        models.ReadingGoal.user_id == user_id,
        models.ReadingGoal.year == year,
    ).first()

    finished_count = (
        db.query(func.count(models.UserBook.id))
        .filter(
            models.UserBook.user_id == user_id,
            models.UserBook.status == "finished",
            func.extract("year", func.coalesce(models.UserBook.date_finished, models.UserBook.created_at)) == year,
        )
        .scalar()
    ) or 0

    return (goal.target if goal else 0), finished_count