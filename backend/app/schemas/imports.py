from pydantic import BaseModel
from typing import Any, List, Optional


class ImportRowError(BaseModel):
    row: int
    error: str
    data: Optional[Any] = None


class ImportResult(BaseModel):
    inserted: int
    updated: int
    skipped: int
    errors: List[ImportRowError]
