from pydantic import BaseModel
from app.models.enums import UserRole


class UserOut(BaseModel):
    id: int
    tg_user_id: int
    username: str | None
    role: UserRole

    class Config:
        from_attributes = True
