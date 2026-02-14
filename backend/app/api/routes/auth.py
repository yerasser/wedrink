from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import TelegramAuthIn, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=TokenOut)
def auth_telegram(payload: TelegramAuthIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_user_id == payload.tg_user_id).one_or_none()
    if not user:
        # whitelist-only
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "not_allowed", "message": "user is not whitelisted"},
        )

    if payload.username is not None and payload.username != user.username:
        user.username = payload.username
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(sub=str(user.id), role=str(user.role.value))
    return TokenOut(access_token=token)
