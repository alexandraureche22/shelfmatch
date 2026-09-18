from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas, models, auth
from ..database import get_db

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("/current", response_model=schemas.ReadingGoalOut)
def get_current_goal(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Obiectivul pentru anul curent, plus câte cărți ai terminat deja anul ăsta."""
    year = date.today().year
    target, finished_count = crud.get_reading_goal(db, current_user.id, year)
    return {"year": year, "target": target, "finished_count": finished_count}


@router.post("/", response_model=schemas.ReadingGoalOut)
def set_goal(
    payload: schemas.ReadingGoalSet,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    year = payload.year or date.today().year
    crud.set_reading_goal(db, current_user.id, year, payload.target)
    target, finished_count = crud.get_reading_goal(db, current_user.id, year)
    return {"year": year, "target": target, "finished_count": finished_count}