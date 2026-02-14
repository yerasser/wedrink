from sqlalchemy import ForeignKey, Numeric, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Inventory(Base):
    __tablename__ = "inventory"

    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id"),
        primary_key=True,
        nullable=False,
    )

    start_qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, server_default="0")
    on_hand_qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, server_default="0")
    min_qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, server_default="0")

    purchase_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    purchase_pack_qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, server_default="1")

    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
    )
