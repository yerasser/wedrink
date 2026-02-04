from typing import List, Optional
from pydantic import BaseModel


class OCRItem(BaseModel):
    code: int
    qty: float



class OCRParseResponse(BaseModel):
    items: List[OCRItem]
