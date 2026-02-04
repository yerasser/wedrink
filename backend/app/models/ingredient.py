from typing import Optional, List

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Ingredient(Base):
    __tablename__ = "ingredient"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    stock: Mapped[Optional["Stock"]] = relationship(
        back_populates="ingredient", uselist=False, cascade="all, delete-orphan"
    )
    recipe_rows: Mapped[List["Recipe"]] = relationship(back_populates="ingredient")
