from sqlalchemy import Enum, ForeignKey, Integer, Text, TIMESTAMP, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ReceiptStatus

class Receipt(Base):
    __tablename__ = "receipts"
    __table_args__ = (Index("ix_receipts_user_id_created_at", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    status: Mapped[ReceiptStatus] = mapped_column(Enum(ReceiptStatus, name="receipt_status"), nullable=False)

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    ocr_started_at: Mapped[str | None] = mapped_column(TIMESTAMP, nullable=True)
    ocr_finished_at: Mapped[str | None] = mapped_column(TIMESTAMP, nullable=True)

    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
