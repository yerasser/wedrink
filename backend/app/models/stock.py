from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Stock(Base):
    __tablename__ = "stock"
    __table_args__ = (
        UniqueConstraint("ingredient_id", name="uq_stock_ingredient"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredient.id", ondelete="CASCADE"),
        nullable=False,
    )

    start: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    norm: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    ingredient: Mapped["Ingredient"] = relationship(back_populates="stock")
