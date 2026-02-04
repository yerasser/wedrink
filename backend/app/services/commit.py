from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.receipt import Receipt
from app.models.receipt_item import ReceiptItem
from app.models.recipe import Recipe
from app.models.stock import Stock


async def commit_receipt(db: AsyncSession, receipt_id: int) -> list[dict]:
    receipt_exists = (await db.execute(
        select(Receipt.id).where(Receipt.id == receipt_id)
    )).scalar_one_or_none()

    if receipt_exists is None:
        raise HTTPException(status_code=404, detail="Receipt not found")

    rows = (await db.execute(
        select(
            Recipe.ingredient_id.label("ingredient_id"),
            func.sum(ReceiptItem.amount * Recipe.qty).label("need"),
        )
        .select_from(ReceiptItem)
        .join(Recipe, Recipe.product_id == ReceiptItem.product_id)
        .where(ReceiptItem.receipt_id == receipt_id)
        .group_by(Recipe.ingredient_id)
    )).all()

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="Nothing to commit: receipt has no items or recipes are missing",
        )

    need_map = {int(r.ingredient_id): float(r.need) for r in rows if r.need is not None}
    if not need_map:
        raise HTTPException(status_code=400, detail="Nothing to commit")

    result_lines: list[dict] = []

    async with db.begin_nested():  # async transaction
        stock_rows = (await db.execute(
            select(Stock)
            .where(Stock.ingredient_id.in_(list(need_map.keys())))
            .with_for_update()  # locks rows
        )).scalars().all()

        stock_by_ing = {s.ingredient_id: s for s in stock_rows}

        missing = [ing_id for ing_id in need_map.keys() if ing_id not in stock_by_ing]
        if missing:
            raise HTTPException(
                status_code=400,
                detail={"message": "Some ingredients are missing in stock", "ingredient_ids": missing},
            )

        not_enough = []
        for ing_id, need in need_map.items():
            s = stock_by_ing[ing_id]
            if float(s.current) < need:
                not_enough.append(
                    {"ingredient_id": ing_id, "need": need, "current": float(s.current)}
                )

        if not_enough:
            raise HTTPException(
                status_code=409,
                detail={"message": "Not enough stock to commit", "items": not_enough},
            )

        for ing_id, need in need_map.items():
            s = stock_by_ing[ing_id]
            before = float(s.current)
            s.current = s.current - need
            after = float(s.current)

            result_lines.append(
                {
                    "ingredient_id": ing_id,
                    "used": float(need),
                    "before": before,
                    "after": after,
                    "norm": float(s.norm),
                    "is_low": after <= float(s.norm),
                }
            )

    return result_lines
