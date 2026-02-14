from pydantic import BaseModel
from app.models.enums import UserRole


class UserCreate(BaseModel):
    tg_user_id: int
    username: str | None = None
    role: UserRole


class UserUpdate(BaseModel):
    username: str | None = None
    role: UserRole | None = None


class UserOut(BaseModel):
    id: int
    tg_user_id: int
    username: str | None
    role: UserRole

    class Config:
        from_attributes = True
