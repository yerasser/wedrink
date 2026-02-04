from sqlalchemy import ForeignKey, Integer, UniqueConstraint, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Recipe(Base):
    __tablename__ = "recipe"
    __table_args__ = (
        UniqueConstraint("product_id", "ingredient_id", name="uq_recipe_product_ingredient"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    product_id: Mapped[int] = mapped_column(ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredient.id", ondelete="CASCADE"), nullable=False)

    qty: Mapped[float] = mapped_column(Float, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="recipe_rows")
    ingredient: Mapped["Ingredient"] = relationship(back_populates="recipe_rows")
