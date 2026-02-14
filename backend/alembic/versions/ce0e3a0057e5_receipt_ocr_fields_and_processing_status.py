"""receipt ocr fields and processing status

Revision ID: ce0e3a0057e5
Revises: 187f4b80eba6
Create Date: 2026-02-09 01:02:20.454314

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce0e3a0057e5'
down_revision: Union[str, Sequence[str], None] = '187f4b80eba6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE receipt_status ADD VALUE IF NOT EXISTS 'processing'")

    op.add_column("receipts", sa.Column("ocr_error", sa.Text(), nullable=True))
    op.add_column("receipts", sa.Column("ocr_started_at", sa.TIMESTAMP(), nullable=True))
    op.add_column("receipts", sa.Column("ocr_finished_at", sa.TIMESTAMP(), nullable=True))
    pass


def downgrade() -> None:
    op.drop_column("receipts", "ocr_finished_at")
    op.drop_column("receipts", "ocr_started_at")
    op.drop_column("receipts", "ocr_error")
    pass
