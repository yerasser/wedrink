from pydantic import BaseModel, Field


class IngredientOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class IngredientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class IngredientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
