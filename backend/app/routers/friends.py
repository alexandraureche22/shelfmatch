from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, models, auth
from ..database import get_db

router = APIRouter(prefix="/friends", tags=["friends"])


@router.post("/request")
def send_request(
    payload: schemas.FriendRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    friendship, error = crud.send_friend_request(db, current_user.id, payload.email)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"sent": True}


@router.post("/accept/{request_id}")
def accept_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ok = crud.accept_friend_request(db, current_user.id, request_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Friend request not found.")
    return {"accepted": True}


@router.get("/requests", response_model=list[schemas.FriendRequestOut])
def list_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    pending = crud.list_pending_requests(db, current_user.id)
    return [{"id": r.id, "requester": r.requester} for r in pending]


@router.get("/", response_model=list[schemas.FriendOut])
def list_friends(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return crud.list_friends(db, current_user.id)

@router.delete("/{friend_id}")
def remove_friend(
    friend_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ok = crud.remove_friend(db, current_user.id, friend_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Friendship not found.")
    return {"removed": True}