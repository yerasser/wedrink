from sqlalchemy import ForeignKey, Integer, Numeric, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ReceiptItem(Base):
    __tablename__ = "receipt_item"
    __table_args__ = (
        UniqueConstraint("receipt_id", "product_id", name="uq_receiptitem_receipt_product"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipt.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id", ondelete="RESTRICT"), nullable=False)

    amount: Mapped[float] = mapped_column(Float, nullable=False)

    receipt: Mapped["Receipt"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="receipt_items")
