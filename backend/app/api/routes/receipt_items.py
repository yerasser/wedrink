from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.deps import get_db
from app.models.enums import ReceiptStatus
from app.models.product import Product
from app.models.receipt import Receipt
from app.models.receipt_item import ReceiptItem
from app.models.user import User
from app.schemas.match import MatchIn
from app.schemas.receipt_item import ReceiptItemCreate, ReceiptItemOut, ReceiptItemUpdate

router = APIRouter(prefix="/receipts/{receipt_id}/items", tags=["receipt_items"])


def _get_owned_receipt(db: Session, receipt_id: int, user_id: int) -> Receipt:
    r = db.get(Receipt, receipt_id)
    if not r:
        raise HTTPException(404, detail={"error": "not_found", "message": "receipt not found"})
    if r.user_id != user_id:
        raise HTTPException(403, detail={"error": "forbidden", "message": "not your receipt"})
    return r


def _ensure_editable(r: Receipt):
    if r.status == ReceiptStatus.applied:
        raise HTTPException(409, detail={"error": "conflict", "message": "receipt already applied"})


@router.get("", response_model=list[ReceiptItemOut])
def list_items(
    receipt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ = _get_owned_receipt(db, receipt_id, user.id)
    return (
        db.query(ReceiptItem)
        .filter(ReceiptItem.receipt_id == receipt_id)
        .order_by(ReceiptItem.id.asc())
        .all()
    )


@router.post("", response_model=ReceiptItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    receipt_id: int,
    payload: ReceiptItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = _get_owned_receipt(db, receipt_id, user.id)
    _ensure_editable(r)

    it = ReceiptItem(
        receipt_id=receipt_id,
        product_code_raw=payload.product_code_raw,
        qty=payload.qty,
        unit_price=payload.unit_price,
        line_total=payload.line_total,
        product_id=payload.product_id,
    )
    db.add(it)

    # можно пометить чек как edited
    if r.status in (ReceiptStatus.parsed, ReceiptStatus.uploaded):
        r.status = ReceiptStatus.edited
        db.add(r)

    db.commit()
    db.refresh(it)
    return it


@router.patch("/{item_id}", response_model=ReceiptItemOut)
def patch_item(
    receipt_id: int,
    item_id: int,
    payload: ReceiptItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = _get_owned_receipt(db, receipt_id, user.id)
    _ensure_editable(r)

    it = db.get(ReceiptItem, item_id)
    if not it or it.receipt_id != receipt_id:
        raise HTTPException(404, detail={"error": "not_found", "message": "item not found"})
    if it.is_deleted:
        raise HTTPException(409, detail={"error": "conflict", "message": "item is deleted"})

    if payload.product_code_raw is not None:
        it.product_code_raw = payload.product_code_raw
    if payload.qty is not None:
        it.qty = payload.qty
    if payload.unit_price is not None:
        it.unit_price = payload.unit_price
    if payload.line_total is not None:
        it.line_total = payload.line_total
    # allow set/unset
    if payload.product_id is not None or payload.product_id is None:
        it.product_id = payload.product_id

    if r.status in (ReceiptStatus.parsed, ReceiptStatus.uploaded):
        r.status = ReceiptStatus.edited
        db.add(r)

    db.add(it)
    db.commit()
    db.refresh(it)
    return it


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    receipt_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = _get_owned_receipt(db, receipt_id, user.id)
    _ensure_editable(r)

    it = db.get(ReceiptItem, item_id)
    if not it or it.receipt_id != receipt_id:
        raise HTTPException(404, detail={"error": "not_found", "message": "item not found"})

    it.is_deleted = True
    db.add(it)

    if r.status in (ReceiptStatus.parsed, ReceiptStatus.uploaded):
        r.status = ReceiptStatus.edited
        db.add(r)

    db.commit()
    return None


@router.post("/{item_id}/match", response_model=ReceiptItemOut)
def match_item(
    receipt_id: int,
    item_id: int,
    payload: MatchIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = _get_owned_receipt(db, receipt_id, user.id)
    _ensure_editable(r)

    it = db.get(ReceiptItem, item_id)
    if not it or it.receipt_id != receipt_id:
        raise HTTPException(404, detail={"error": "not_found", "message": "item not found"})
    if it.is_deleted:
        raise HTTPException(409, detail={"error": "conflict", "message": "item is deleted"})

    p = db.get(Product, payload.product_id)
    if not p:
        raise HTTPException(404, detail={"error": "not_found", "message": "product not found"})

    it.product_id = p.id

    if r.status in (ReceiptStatus.parsed, ReceiptStatus.uploaded):
        r.status = ReceiptStatus.edited
        db.add(r)

    db.add(it)
    db.commit()
    db.refresh(it)
    return it
