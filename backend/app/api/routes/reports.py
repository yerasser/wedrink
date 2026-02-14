from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, case
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.ingredient import Ingredient
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.schemas.reports import ConsumptionRow, StockRow

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/stock", response_model=list[StockRow])
def report_stock(only_low: bool | None = False, db: Session = Depends(get_db)):
    q = (
        db.query(
            Inventory.ingredient_id.label("ingredient_id"),
            Ingredient.name.label("ingredient_name"),
            Inventory.on_hand_qty.label("on_hand_qty"),
            Inventory.min_qty.label("min_qty"),
            Inventory.purchase_price.label("purchase_price"),
            Inventory.purchase_pack_qty.label("purchase_pack_qty"),
        )
        .join(Ingredient, Ingredient.id == Inventory.ingredient_id)
    )

    if only_low:
        q = q.filter(Inventory.on_hand_qty <= Inventory.min_qty)

    rows = q.order_by(Ingredient.name.asc()).all()
    return [StockRow(**r._asdict()) for r in rows]


@router.get("/consumption", response_model=list[ConsumptionRow])
def report_consumption(
    from_: str | None = None,
    to: str | None = None,
    ingredient_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            InventoryMovement.ingredient_id.label("ingredient_id"),
            Ingredient.name.label("ingredient_name"),

            (func.sum(case((InventoryMovement.qty_delta < 0, -InventoryMovement.qty_delta), else_=0))).label(
                "consumed_qty"
            ),
        )
        .join(Ingredient, Ingredient.id == InventoryMovement.ingredient_id)
    )

    filters = []
    if ingredient_id is not None:
        filters.append(InventoryMovement.ingredient_id == ingredient_id)
    if from_ is not None:
        filters.append(InventoryMovement.created_at >= datetime.fromisoformat(from_))
    if to is not None:
        filters.append(InventoryMovement.created_at <= datetime.fromisoformat(to))

    if filters:
        q = q.filter(and_(*filters))

    rows = q.group_by(InventoryMovement.ingredient_id, Ingredient.name).order_by(Ingredient.name.asc()).all()
    return [ConsumptionRow(**r._asdict()) for r in rows]
