from fastapi import APIRouter, Depends
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