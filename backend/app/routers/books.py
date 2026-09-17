from fastapi import APIRouter, Depends, HTTPException
import httpx
from sqlalchemy.orm import Session
from .. import crud, schemas, google_books, models, auth
from ..database import get_db

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/search")
async def search_books(q: str):
    """Caută cărți prin Google Books, fără să le salveze încă. Public, nu ține de cont."""
    try:
        return await google_books.search_books(q)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(status_code=503, detail="Google Books a limitat request-urile momentan. Mai încearcă în 1-2 minute.")
        raise HTTPException(status_code=502, detail="Google Books nu a răspuns corect.")


@router.post("/", response_model=schemas.BookOut)
def add_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    """Salvează o carte (din rezultatele Google Books sau manual) în catalogul comun."""
    return crud.get_or_create_book(db, book)


@router.post("/log", response_model=schemas.UserBookOut)
def log_user_book(
    entry: schemas.UserBookCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Adaugă o carte în istoricul personal al user-ului logat."""
    return crud.create_user_book(db, current_user.id, entry)


@router.get("/mine", response_model=list[schemas.UserBookOut])
def my_books(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return crud.list_user_books(db, current_user.id, status)


@router.put("/log/{entry_id}", response_model=schemas.UserBookOut)
def edit_user_book(
    entry_id: int,
    updates: schemas.UserBookUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Editează o intrare din istoricul personal (rating, date, status) — inclusiv după 'finished'."""
    entry = crud.update_user_book(db, current_user.id, entry_id, updates)
    if not entry:
        raise HTTPException(status_code=404, detail="I don't have that book in your list.")
    return entry


@router.delete("/log/{entry_id}")
def delete_user_book(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ok = crud.delete_user_book(db, current_user.id, entry_id)
    if not ok:
        raise HTTPException(status_code=404, detail="I don't have that book in your list.")
    return {"deleted": True}