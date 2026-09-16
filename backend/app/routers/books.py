from fastapi import APIRouter, Depends, HTTPException
import httpx
from sqlalchemy.orm import Session
from .. import crud, schemas, google_books
from ..database import get_db

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/search")
async def search_books(q: str):
    """Caută cărți prin Google Books, fără să le salveze încă."""
    try:
        return await google_books.search_books(q)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(status_code=503, detail="Google Books a limitat request-urile momentan. Mai încearcă în 1-2 minute.")
        raise HTTPException(status_code=502, detail="Google Books nu a răspuns corect.")


@router.post("/", response_model=schemas.BookOut)
def add_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    """Salvează o carte (din rezultatele Google Books sau manual) în tabela books."""
    return crud.get_or_create_book(db, book)


@router.post("/log", response_model=schemas.UserBookOut)
def log_user_book(entry: schemas.UserBookCreate, db: Session = Depends(get_db)):
    """Adaugă o carte în istoricul/lista utilizatorului (status: reading/finished/wishlist)."""
    return crud.create_user_book(db, entry)


@router.get("/mine", response_model=list[schemas.UserBookOut])
def my_books(status: str | None = None, db: Session = Depends(get_db)):
    return crud.list_user_books(db, status)