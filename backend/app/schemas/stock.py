from typing import Optional
from pydantic import BaseModel


class StockOut(BaseModel):
    ingredient_id: int
    ingredient_name: str
    start: float
    current: float
    norm: float


class StockAlertOut(BaseModel):
    ingredient_id: int
    ingredient_name: str

    start: float
    current: float
    spent: float
    spent_pct: float

    status: str
