from pydantic import BaseModel, Field


class RecipeItemIn(BaseModel):
    ingredient_id: int
    qty: float = Field(gt=0)


class RecipeItemOut(BaseModel):
    ingredient_id: int
    qty: float

    class Config:
        from_attributes = True
