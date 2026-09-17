from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas, models, auth
from ..database import get_db

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/genres", response_model=list[schemas.GenreStatOut])
def genre_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Datele brute pentru graficele din dashboard, doar pentru user-ul curent."""
    return crud.get_genre_stats(db, current_user.id)