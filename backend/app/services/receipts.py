from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.receipt import Receipt
from app.models.receipt_item import ReceiptItem
from app.schemas.receipts import ReceiptCreateIn


async def get_receipt(db: AsyncSession, receipt_id: int) -> Receipt:
    stmt = (
        select(Receipt)
        .options(selectinload(Receipt.items))
        .where(Receipt.id == receipt_id)
    )
    return (await db.execute(stmt)).scalar_one()

async def create_receipt(db: AsyncSession, payload: ReceiptCreateIn) -> Receipt:
    receipt = Receipt(
        items=[ReceiptItem(product_id=i.product_id, amount=i.amount) for i in payload.items]
    )
    db.add(receipt)
    await db.commit()
    return await get_receipt(db, receipt.id)  # перечитать с items
