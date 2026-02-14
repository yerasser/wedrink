from datetime import datetime

from pydantic import BaseModel
from app.models.enums import ReceiptStatus


class ReceiptOut(BaseModel):
    id: int
    user_id: int
    status: ReceiptStatus
    raw_text: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ReceiptCreateOut(BaseModel):
    id: int
    status: ReceiptStatus

    class Config:
        from_attributes = True
