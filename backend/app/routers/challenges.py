from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, models, auth
from ..database import get_db

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.get("/", response_model=list[schemas.ChallengeOut])
def list_challenges(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Challenge-uri oficiale (publice) + challenge-uri ale prietenilor tăi + ale tale."""
    return crud.list_challenges(db, current_user.id)


@router.post("/", response_model=schemas.ChallengeOut)
def create_challenge(
    payload: schemas.ChallengeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Creezi un challenge — vizibil doar prietenilor tăi (și ție)."""
    challenge = crud.create_challenge(db, current_user.id, payload)
    return {
        "id": challenge.id,
        "title": challenge.title,
        "description": challenge.description,
        "month": challenge.month,
        "visibility": challenge.visibility,
        "creator_email": current_user.email,
    }


@router.post("/{challenge_id}/complete")
def complete_challenge(
    challenge_id: int,
    payload: schemas.ChallengeCompleteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Marchezi challenge-ul ca terminat, alegând o carte din biblioteca ta."""
    completion, error = crud.complete_challenge(db, current_user.id, challenge_id, payload.user_book_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"completed": True}


@router.get("/{challenge_id}/completions", response_model=list[schemas.ChallengeCompletionOut])
def get_completions(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Ce cărți au ales tu și prietenii tăi pentru acest challenge."""
    return crud.get_challenge_completions(db, current_user.id, challenge_id)