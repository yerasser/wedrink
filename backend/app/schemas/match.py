from pydantic import BaseModel


class MatchIn(BaseModel):
    product_id: int
