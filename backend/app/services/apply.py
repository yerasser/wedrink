from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ReceiptStatus
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.recipe import Recipe
from app.models.receipt import Receipt
from app.models.receipt_item import ReceiptItem
from decimal import Decimal



def apply_receipt(db: Session, *, receipt_id: int, user_id: int) -> Receipt:
    receipt = db.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(404, detail={"error": "not_found", "message": "receipt not found"})
    if receipt.user_id != user_id:
        raise HTTPException(403, detail={"error": "forbidden", "message": "not your receipt"})
    if receipt.status == ReceiptStatus.applied:
        raise HTTPException(409, detail={"error": "conflict", "message": "receipt already applied"})

    items = (
        db.query(ReceiptItem)
        .filter(
            ReceiptItem.receipt_id == receipt_id,
            ReceiptItem.is_deleted == False,  # noqa: E712
        )
        .all()
    )
    if not items:
        raise HTTPException(409, detail={"error": "conflict", "message": "no items to apply"})

    missing = [it.id for it in items if it.product_id is None]
    if missing:
        raise HTTPException(
            409,
            detail={
                "error": "unmatched_items",
                "message": "apply forbidden: some items have no product_id",
                "item_ids": missing,
            },
        )

    # Собираем все рецепты для продуктов одним запросом
    product_ids = sorted({it.product_id for it in items if it.product_id is not None})
    recipes = db.query(Recipe).filter(Recipe.product_id.in_(product_ids)).all()

    # map: product_id -> list[Recipe]
    recipe_map: dict[int, list[Recipe]] = {}
    for r in recipes:
        recipe_map.setdefault(r.product_id, []).append(r)

    # Если у продукта нет рецепта — запрещаем (иначе непонятно что списывать)
    no_recipe = [pid for pid in product_ids if pid not in recipe_map]
    if no_recipe:
        raise HTTPException(
            409,
            detail={"error": "no_recipe", "message": "apply forbidden: product has no recipe", "product_ids": no_recipe},
        )

    # Считаем дельты по ингредиентам (агрегация) чтобы делать меньше updates
    # delta = sum( -(item.qty * recipe.qty) )
    agg: dict[int, Decimal] = {}
    for it in items:
        for r in recipe_map[it.product_id]:
            ing_id = r.ingredient_id
            delta = Decimal(-(Decimal(it.qty) * Decimal(r.qty)))
            agg[ing_id] = agg.get(ing_id, Decimal(0)) + delta

    # Транзакция: lock inventory rows + insert movements + update inventory + update receipt
    with db.begin_nested():
        # lock receipt row тоже полезно
        db.execute(
            select(Receipt.id)
            .where(Receipt.id == receipt_id)
            .with_for_update()
        )

        # lock inventory rows
        inv_rows = (
            db.execute(
                select(Inventory)
                .where(Inventory.ingredient_id.in_(list(agg.keys())))
                .with_for_update()
            )
            .scalars()
            .all()
        )
        inv_map = {inv.ingredient_id: inv for inv in inv_rows}

        missing_inv = [ing_id for ing_id in agg.keys() if ing_id not in inv_map]
        if missing_inv:
            raise HTTPException(
                409,
                detail={"error": "inventory_missing", "message": "inventory row missing for ingredient", "ingredient_ids": missing_inv},
            )

        # insert movements + update inventory
        for ing_id, delta in agg.items():
            mv = InventoryMovement(
                ingredient_id=ing_id,
                qty_delta=delta,
                source_receipt_id=receipt_id,
                created_by=user_id,
            )
            db.add(mv)

            inv = inv_map[ing_id]
            inv.on_hand_qty = inv.on_hand_qty + delta
            db.add(inv)

        receipt.status = ReceiptStatus.applied
        db.add(receipt)

    db.commit()
    db.refresh(receipt)
    return receipt
