from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.core.deps import get_db
from app.models.user import User
from app.schemas.user_admin import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut], dependencies=[Depends(require_role("admin"))])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id.asc()).all()


@router.post("", response_model=UserOut, status_code=201, dependencies=[Depends(require_role("admin"))])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    u = User(tg_user_id=payload.tg_user_id, username=payload.username, role=payload.role)
    db.add(u)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, detail={"error": "conflict", "message": "tg_user_id must be unique"})
    db.refresh(u)
    return u


@router.patch("/{user_id}", response_model=UserOut, dependencies=[Depends(require_role("admin"))])
def patch_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, detail={"error": "not_found", "message": "user not found"})
    if payload.username is not None:
        u.username = payload.username
    if payload.role is not None:
        u.role = payload.role
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, detail={"error": "not_found", "message": "user not found"})
    db.delete(u)
    db.commit()
    return None
