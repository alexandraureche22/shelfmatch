from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/genres", response_model=list[schemas.GenreStatOut])
def genre_stats(db: Session = Depends(get_db)):
    """Datele brute pentru graficele din dashboard: pagini/zi și rating mediu, per gen."""
    return crud.get_genre_stats(db)
