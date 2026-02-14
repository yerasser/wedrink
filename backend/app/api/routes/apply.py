from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.deps import get_db
from app.models.user import User
from app.schemas.receipt import ReceiptOut
from app.services.apply import apply_receipt

router = APIRouter(prefix="/receipts", tags=["apply"])


@router.post("/{receipt_id}/apply", response_model=ReceiptOut)
def apply(receipt_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return apply_receipt(db, receipt_id=receipt_id, user_id=user.id)
