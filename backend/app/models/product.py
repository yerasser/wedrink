from typing import List

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    recipe_rows: Mapped[List["Recipe"]] = relationship(back_populates="product")
    receipt_items: Mapped[List["ReceiptItem"]] = relationship(back_populates="product")