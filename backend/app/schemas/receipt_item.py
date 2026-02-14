from datetime import datetime

from pydantic import BaseModel, Field


class ReceiptItemOut(BaseModel):
    id: int
    receipt_id: int
    product_code_raw: str
    qty: float
    unit_price: float | None
    line_total: float | None
    product_id: int | None
    is_deleted: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class ReceiptItemCreate(BaseModel):
    product_code_raw: str = Field(min_length=1, max_length=200)
    qty: float = Field(gt=0)
    unit_price: float | None = None
    line_total: float | None = None
    product_id: int | None = None


class ReceiptItemUpdate(BaseModel):
    product_code_raw: str | None = Field(default=None, min_length=1, max_length=200)
    qty: float | None = Field(default=None, gt=0)
    unit_price: float | None = None
    line_total: float | None = None
    product_id: int | None = None  # можно ставить/снимать
