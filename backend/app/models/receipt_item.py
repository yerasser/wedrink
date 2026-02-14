from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, Text, TIMESTAMP, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReceiptItem(Base):
    __tablename__ = "receipt_items"
    __table_args__ = (
        Index("ix_receipt_items_receipt_id", "receipt_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipts.id"), nullable=False)

    product_code_raw: Mapped[str] = mapped_column(Text, nullable=False)

    qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)

    unit_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    line_total: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
    )
