from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_role
from app.core.deps import get_db
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.ingredient import Ingredient
from app.models.user import User
from app.schemas.inventory import InventoryOut, InventoryUpdate
from app.schemas.movement import MovementCreate, MovementOut

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=list[InventoryOut])
def list_inventory(db: Session = Depends(get_db)):
    return db.query(Inventory).order_by(Inventory.ingredient_id.asc()).all()


@router.get("/{ingredient_id}", response_model=InventoryOut)
def get_inventory(ingredient_id: int, db: Session = Depends(get_db)):
    inv = db.get(Inventory, ingredient_id)
    if not inv:
        raise HTTPException(404, detail={"error": "not_found", "message": "inventory row not found"})
    return inv


@router.patch(
    "/{ingredient_id}",
    response_model=InventoryOut,
    dependencies=[Depends(require_role("admin"))],
)
def patch_inventory(ingredient_id: int, payload: InventoryUpdate, db: Session = Depends(get_db)):
    inv = db.get(Inventory, ingredient_id)
    if not inv:
        raise HTTPException(404, detail={"error": "not_found", "message": "inventory row not found"})

    if payload.min_qty is not None:
        inv.min_qty = payload.min_qty
    if payload.purchase_price is not None:
        inv.purchase_price = payload.purchase_price
    if payload.purchase_pack_qty is not None:
        inv.purchase_pack_qty = payload.purchase_pack_qty

    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.post(
    "/movements",
    response_model=MovementOut,
    status_code=status.HTTP_201_CREATED,
)
def create_movement(
    payload: MovementCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # operator/admin allowed by current_user (оба имеют токен)
    ing = db.get(Ingredient, payload.ingredient_id)
    if not ing:
        raise HTTPException(404, detail={"error": "not_found", "message": "ingredient not found"})

    # inventory row must exist
    inv = db.get(Inventory, payload.ingredient_id)
    if not inv:
        raise HTTPException(409, detail={"error": "conflict", "message": "inventory row missing for ingredient"})

    with db.begin():
        mv = InventoryMovement(
            ingredient_id=payload.ingredient_id,
            qty_delta=payload.qty_delta,
            source_receipt_id=payload.source_receipt_id,
            created_by=user.id,
        )
        db.add(mv)

        # update on_hand
        inv.on_hand_qty = inv.on_hand_qty + payload.qty_delta
        db.add(inv)

    db.refresh(mv)
    return mv


@router.get("/movements", response_model=list[MovementOut])
def list_movements(
    from_: str | None = None,
    to: str | None = None,
    ingredient_id: int | None = None,
    source_receipt_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(InventoryMovement)

    filters = []
    if ingredient_id is not None:
        filters.append(InventoryMovement.ingredient_id == ingredient_id)
    if source_receipt_id is not None:
        filters.append(InventoryMovement.source_receipt_id == source_receipt_id)

    # даты ISO: "2026-02-01" или "2026-02-01T00:00:00"
    if from_ is not None:
        dt_from = datetime.fromisoformat(from_)
        filters.append(InventoryMovement.created_at >= dt_from)
    if to is not None:
        dt_to = datetime.fromisoformat(to)
        filters.append(InventoryMovement.created_at <= dt_to)

    if filters:
        q = q.filter(and_(*filters))

    return q.order_by(InventoryMovement.created_at.desc()).all()
