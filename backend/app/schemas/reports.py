from pydantic import BaseModel


class StockRow(BaseModel):
    ingredient_id: int
    ingredient_name: str
    on_hand_qty: float
    min_qty: float
    purchase_price: float
    purchase_pack_qty: float

class ConsumptionRow(BaseModel):
    ingredient_id: int
    ingredient_name: str
    consumed_qty: float
