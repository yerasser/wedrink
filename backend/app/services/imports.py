from __future__ import annotations

from typing import Tuple, List, Dict, Any
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient
from app.models.product import Product
from app.models.recipe import Recipe
from app.models.stock import Stock


def _require_cols(df, cols: list[str]) -> list[str]:
    missing = [c for c in cols if c not in df.columns]
    return missing


async def _sync_sequence(db: AsyncSession, table_name: str, pk_col: str = "id") -> None:
    await db.execute(
        text(
            f"""
            SELECT setval(
              pg_get_serial_sequence('{table_name}', '{pk_col}'),
              COALESCE((SELECT MAX({pk_col}) FROM {table_name}), 1)
            );
            """
        )
    )


async def import_ingredients(db: AsyncSession, df) -> Tuple[int, int, int, List[Dict[str, Any]]]:
    missing = _require_cols(df, ["id", "name"])
    if missing:
        return 0, 0, 0, [{"row": 1, "error": f"Missing columns: {missing}", "data": list(df.columns)}]

    inserted = updated = skipped = 0
    errors = []

    for idx, row in df.iterrows():
        excel_row = int(idx) + 2  # +1 заголовок, +1 1-based
        try:
            rid = int(row["id"])
            name = str(row["name"]).strip()
            if not name:
                skipped += 1
                continue

            obj = (await db.execute(select(Ingredient).where(Ingredient.id == rid))).scalar_one_or_none()
            if obj is None:
                db.add(Ingredient(id=rid, name=name))
                inserted += 1
            else:
                if obj.name != name:
                    obj.name = name
                    updated += 1
                else:
                    skipped += 1

        except Exception as e:
            errors.append({"row": excel_row, "error": str(e), "data": {"id": row.get("id"), "name": row.get("name")}})

    await db.commit()
    # синхронизируем sequence
    await _sync_sequence(db, Ingredient.__tablename__, "id")
    await db.commit()
    return inserted, updated, skipped, errors


async def import_products(db: AsyncSession, df) -> Tuple[int, int, int, List[Dict[str, Any]]]:
    missing = _require_cols(df, ["id", "name"])
    if missing:
        return 0, 0, 0, [{"row": 1, "error": f"Missing columns: {missing}", "data": list(df.columns)}]

    inserted = updated = skipped = 0
    errors = []

    for idx, row in df.iterrows():
        excel_row = int(idx) + 2
        try:
            rid = int(row["id"])
            name = str(row["name"]).strip()
            if not name:
                skipped += 1
                continue

            obj = (await db.execute(select(Product).where(Product.id == rid))).scalar_one_or_none()
            if obj is None:
                db.add(Product(id=rid, name=name))
                inserted += 1
            else:
                if obj.name != name:
                    obj.name = name
                    updated += 1
                else:
                    skipped += 1

        except Exception as e:
            errors.append({"row": excel_row, "error": str(e), "data": {"id": row.get("id"), "name": row.get("name")}})

    await db.commit()
    await _sync_sequence(db, Product.__tablename__, "id")
    await db.commit()
    return inserted, updated, skipped, errors


async def import_recipes(db: AsyncSession, df) -> Tuple[int, int, int, List[Dict[str, Any]]]:
    missing = _require_cols(df, ["product_id", "ingredient_id", "qty"])
    if missing:
        return 0, 0, 0, [{"row": 1, "error": f"Missing columns: {missing}", "data": list(df.columns)}]

    inserted = updated = skipped = 0
    errors = []

    for idx, row in df.iterrows():
        excel_row = int(idx) + 2
        try:
            pid = int(row["product_id"])
            iid = int(row["ingredient_id"])
            qty = float(row["qty"])

            obj = (
                await db.execute(
                    select(Recipe).where(Recipe.product_id == pid, Recipe.ingredient_id == iid)
                )
            ).scalar_one_or_none()

            if obj is None:
                db.add(Recipe(product_id=pid, ingredient_id=iid, qty=qty))
                inserted += 1
            else:
                if float(obj.qty) != qty:
                    obj.qty = qty
                    updated += 1
                else:
                    skipped += 1

        except Exception as e:
            errors.append(
                {
                    "row": excel_row,
                    "error": str(e),
                    "data": {
                        "product_id": row.get("product_id"),
                        "ingredient_id": row.get("ingredient_id"),
                        "qty": row.get("qty"),
                    },
                }
            )

    await db.commit()
    return inserted, updated, skipped, errors


async def import_stock(db: AsyncSession, df) -> Tuple[int, int, int, List[Dict[str, Any]]]:
    missing = _require_cols(df, ["ingredient_id", "start", "current", "norm"])
    if missing:
        return 0, 0, 0, [{"row": 1, "error": f"Missing columns: {missing}", "data": list(df.columns)}]

    inserted = updated = skipped = 0
    errors = []

    for idx, row in df.iterrows():
        excel_row = int(idx) + 2
        try:
            iid = int(row["ingredient_id"])
            start = float(row["start"])
            current = float(row["current"])
            norm = float(row["norm"])

            obj = (await db.execute(select(Stock).where(Stock.ingredient_id == iid))).scalar_one_or_none()
            if obj is None:
                db.add(Stock(ingredient_id=iid, start=start, current=current, norm=norm))
                inserted += 1
            else:
                changed = False
                if float(obj.start) != start:
                    obj.start = start
                    changed = True
                if float(obj.current) != current:
                    obj.current = current
                    changed = True
                if float(obj.norm) != norm:
                    obj.norm = norm
                    changed = True

                if changed:
                    updated += 1
                else:
                    skipped += 1

        except Exception as e:
            errors.append(
                {
                    "row": excel_row,
                    "error": str(e),
                    "data": {
                        "ingredient_id": row.get("ingredient_id"),
                        "start": row.get("start"),
                        "current": row.get("current"),
                        "norm": row.get("norm"),
                    },
                }
            )

    await db.commit()
    return inserted, updated, skipped, errors
