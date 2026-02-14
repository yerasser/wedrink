from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ReceiptStatus
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.receipt import Receipt


def rollback_receipt(db: Session, *, receipt_id: int, user_id) -> Receipt:
    receipt = db.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(404, detail={"error": "not_found", "message": "receipt not found"})
    if receipt.status != ReceiptStatus.applied:
        raise HTTPException(409, detail={"error": "conflict", "message": "receipt is not applied"})

    orig = (
        db.query(InventoryMovement)
        .filter(InventoryMovement.source_receipt_id == receipt_id)
        .order_by(InventoryMovement.id.asc())
        .all()
    )
    if not orig:
        raise HTTPException(409, detail={"error": "conflict", "message": "no movements to rollback"})

    ing_ids = sorted({m.ingredient_id for m in orig})

    with db.begin_nested():
        # lock receipt
        db.execute(select(Receipt.id).where(Receipt.id == receipt_id).with_for_update())

        # lock inventory rows
        inv_rows = (
            db.execute(
                select(Inventory)
                .where(Inventory.ingredient_id.in_(ing_ids))
                .with_for_update()
            )
            .scalars()
            .all()
        )
        inv_map = {inv.ingredient_id: inv for inv in inv_rows}
        missing_inv = [i for i in ing_ids if i not in inv_map]
        if missing_inv:
            raise HTTPException(
                409,
                detail={"error": "inventory_missing", "message": "inventory row missing for ingredient", "ingredient_ids": missing_inv},
            )

        # compensate
        for m in orig:
            comp_delta = -float(m.qty_delta)
            db.add(
                InventoryMovement(
                    ingredient_id=m.ingredient_id,
                    qty_delta=comp_delta,
                    source_receipt_id=None,
                    created_by=user_id,
                )
            )
            inv = inv_map[m.ingredient_id]
            inv.on_hand_qty = inv.on_hand_qty + Decimal(comp_delta)
            db.add(inv)

        receipt.status = ReceiptStatus.edited
        db.add(receipt)

    db.commit()
    db.refresh(receipt)
    return receipt
