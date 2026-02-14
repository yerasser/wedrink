from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require_role, get_current_user
from app.core.deps import get_db
from app.models.user import User
from app.schemas.receipt import ReceiptOut
from app.services.rollback import rollback_receipt

router = APIRouter(prefix="/receipts", tags=["rollback"])


@router.post("/{receipt_id}/rollback", response_model=ReceiptOut)
def rollback(receipt_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return rollback_receipt(db, receipt_id=receipt_id, user_id=user.id)
