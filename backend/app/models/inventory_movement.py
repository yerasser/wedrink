from sqlalchemy import ForeignKey, Integer, Numeric, TIMESTAMP, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        Index("ix_inventory_movements_ingredient_id_created_at", "ingredient_id", "created_at"),
        Index("ix_inventory_movements_source_receipt_id", "source_receipt_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), nullable=False)

    qty_delta: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)

    source_receipt_id: Mapped[int | None] = mapped_column(ForeignKey("receipts.id"), nullable=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    created_at: Mapped[str] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
    )
