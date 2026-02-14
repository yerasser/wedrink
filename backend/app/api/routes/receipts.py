import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.deps import get_db
from app.models.enums import ReceiptStatus
from app.models.receipt import Receipt
from app.models.user import User
from app.schemas.receipt import ReceiptCreateOut, ReceiptOut
from app.services.storage import put_object
from app.tasks.ocr_tasks import ocr_process_receipt

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.post("", response_model=ReceiptCreateOut, status_code=201)
def create_receipt(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = Receipt(user_id=user.id, status=ReceiptStatus.uploaded, raw_text=None)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r

@router.post("/{receipt_id}/ocr", response_model=ReceiptOut, status_code=status.HTTP_202_ACCEPTED)
def enqueue_ocr(
    receipt_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = db.get(Receipt, receipt_id)
    if not r:
        raise HTTPException(404, detail={"error": "not_found", "message": "receipt not found"})
    if r.user_id != user.id:
        raise HTTPException(403, detail={"error": "forbidden", "message": "not your receipt"})
    if r.status == ReceiptStatus.applied:
        raise HTTPException(409, detail={"error": "conflict", "message": "receipt already applied"})
    if r.status == ReceiptStatus.processing:
        raise HTTPException(409, detail={"error": "conflict", "message": "ocr already processing"})

    data = file.file.read()
    if not data:
        raise HTTPException(400, detail={"error": "bad_request", "message": "empty file"})

    # загрузка в MinIO
    key = f"receipts/{receipt_id}/{uuid.uuid4().hex}"
    put_object(key, data, content_type=file.content_type)

    # ставим статус processing сразу (чтобы пользователь видел)
    r.status = ReceiptStatus.processing
    db.add(r)
    db.commit()
    db.refresh(r)

    # enqueue задача
    ocr_process_receipt.delay(receipt_id, key)

    return r

@router.get("", response_model=list[ReceiptOut])
def list_receipts(
    status: ReceiptStatus | None = None,
    from_: str | None = None,
    to: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Receipt).filter(Receipt.user_id == user.id)

    filters = []
    if status is not None:
        filters.append(Receipt.status == status)

    if from_ is not None:
        dt_from = datetime.fromisoformat(from_)
        filters.append(Receipt.created_at >= dt_from)
    if to is not None:
        dt_to = datetime.fromisoformat(to)
        filters.append(Receipt.created_at <= dt_to)

    if filters:
        q = q.filter(and_(*filters))

    return q.order_by(Receipt.created_at.desc()).all()


@router.get("/{receipt_id}", response_model=ReceiptOut)
def get_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = db.get(Receipt, receipt_id)
    if not r:
        raise HTTPException(404, detail={"error": "not_found", "message": "receipt not found"})
    if r.user_id != user.id:
        raise HTTPException(403, detail={"error": "forbidden", "message": "not your receipt"})
    return r
