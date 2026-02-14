from datetime import datetime

from pydantic import BaseModel, Field


class MovementCreate(BaseModel):
    ingredient_id: int
    qty_delta: float = Field(ne=0)
    source_receipt_id: int | None = None  # руками обычно null


class MovementOut(BaseModel):
    id: int
    ingredient_id: int
    qty_delta: float
    source_receipt_id: int | None
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
