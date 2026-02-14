from pydantic import BaseModel


class TelegramAuthIn(BaseModel):
    tg_user_id: int
    username: str | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
