from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.receipts import ReceiptCreateIn, ReceiptOut, ReceiptItemOut
from app.schemas.commit import CommitResult
from app.services.receipts import create_receipt
from app.services.commit import commit_receipt

router = APIRouter()


@router.post("", response_model=ReceiptOut)
async def create(payload: ReceiptCreateIn, db: AsyncSession = Depends(get_db)):
    receipt = await create_receipt(db, payload)

    return ReceiptOut(
        id=receipt.id,
        created_at=receipt.created_at,
        items=[
            ReceiptItemOut(product_id=i.product_id, amount=i.amount)
            for i in receipt.items
        ],
    )

@router.post("/{receipt_id}/commit", response_model=CommitResult)
async def commit(receipt_id: int, db: AsyncSession = Depends(get_db)):
    lines = await commit_receipt(db, receipt_id)
    return {"receipt_id": receipt_id, "lines": lines}

