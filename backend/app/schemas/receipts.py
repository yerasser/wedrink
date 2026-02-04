from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, ConfigDict


class ReceiptItemIn(BaseModel):
    product_id: int
    amount: float = Field(gt=0)


class ReceiptCreateIn(BaseModel):
    items: List[ReceiptItemIn] = Field(min_length=1)


class ReceiptItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    amount: float


class ReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    items: List[ReceiptItemOut]
