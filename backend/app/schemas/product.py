from pydantic import BaseModel, Field


class ProductOut(BaseModel):
    id: int
    code: str
    name: str | None

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    name: str | None = Field(default=None, max_length=200)


class ProductUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = Field(default=None, max_length=200)
