from datetime import datetime

from pydantic import BaseModel, Field


class InventoryOut(BaseModel):
    ingredient_id: int
    start_qty: float
    on_hand_qty: float
    min_qty: float
    purchase_price: float
    purchase_pack_qty: float
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryUpdate(BaseModel):
    min_qty: float | None = None
    purchase_price: float | None = None
    purchase_pack_qty: float | None = Field(default=None, gt=0)
