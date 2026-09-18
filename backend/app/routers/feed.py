from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, models, auth
from ..database import get_db

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/", response_model=list[schemas.FeedItemOut])
def get_feed(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Activitatea recentă a prietenilor: cărți terminate/în curs, cu rating dacă există."""
    return crud.get_feed(db, current_user.id)


@router.get("/{user_book_id}/like", response_model=schemas.LikeOut)
def get_like(
    user_book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not crud.can_interact_with_user_book(db, current_user.id, user_book_id):
        raise HTTPException(status_code=404, detail="Not found.")
    liked, count = crud.get_like_info(db, current_user.id, user_book_id)
    return {"liked": liked, "like_count": count}


@router.post("/{user_book_id}/like", response_model=schemas.LikeOut)
def toggle_like(
    user_book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not crud.can_interact_with_user_book(db, current_user.id, user_book_id):
        raise HTTPException(status_code=404, detail="Not found.")
    liked, count = crud.toggle_like(db, current_user.id, user_book_id)
    return {"liked": liked, "like_count": count}


@router.get("/{user_book_id}/comments", response_model=list[schemas.CommentOut])
def get_comments(
    user_book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not crud.can_interact_with_user_book(db, current_user.id, user_book_id):
        raise HTTPException(status_code=404, detail="Not found.")
    return crud.list_comments(db, user_book_id)


@router.post("/{user_book_id}/comments", response_model=schemas.CommentOut)
def post_comment(
    user_book_id: int,
    payload: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not crud.can_interact_with_user_book(db, current_user.id, user_book_id):
        raise HTTPException(status_code=404, detail="Not found.")
    crud.add_comment(db, current_user.id, user_book_id, payload.text)
    return {"user_email": current_user.email, "text": payload.text}