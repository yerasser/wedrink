from pydantic import BaseModel
from typing import List


class CommitLine(BaseModel):
    ingredient_id: int
    used: float
    before: float
    after: float
    norm: float
    is_low: bool


class CommitResult(BaseModel):
    receipt_id: int
    lines: List[CommitLine]
