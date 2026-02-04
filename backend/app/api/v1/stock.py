from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.stock import Stock
from app.models.ingredient import Ingredient
from app.schemas.stock import StockOut, StockAlertOut

router = APIRouter()


@router.get("", response_model=List[StockOut])
async def list_stock(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Stock, Ingredient.name)
        .join(Ingredient, Ingredient.id == Stock.ingredient_id)
        .order_by(Ingredient.name.asc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    return [
        StockOut(
            ingredient_id=stock.ingredient_id,
            ingredient_name=name,
            start=float(stock.start),
            current=float(stock.current),
            norm=float(stock.norm),
        )
        for stock, name in rows
    ]


@router.get("/alerts", response_model=List[StockAlertOut])
async def stock_alerts(db: AsyncSession = Depends(get_db)):
    """
    Отчет для телеграм-бота:
    - 30-59% потрачено => "КОНТРОЛЬ"
    - >=60% потрачено => "СРОЧНО"
    Возвращает только эти позиции.
    """
    stmt = (
        select(Stock, Ingredient.name)
        .join(Ingredient, Ingredient.id == Stock.ingredient_id)
    )
    res = await db.execute(stmt)
    rows = res.all()

    out: List[StockAlertOut] = []

    for stock, name in rows:
        start = float(stock.start or 0.0)
        current = float(stock.current or 0.0)

        if start <= 0:
            continue

        spent = start - current
        spent_pct = (spent / start) * 100.0

        if 30.0 <= spent_pct <= 59.0:
            status = "КОНТРОЛЬ"
        elif spent_pct >= 60.0:
            status = "СРОЧНО"
        else:
            continue

        out.append(
            StockAlertOut(
                ingredient_id=stock.ingredient_id,
                ingredient_name=name,
                start=round(start, 3),
                current=round(current, 3),
                spent=round(spent, 3),
                spent_pct=round(spent_pct, 1),
                status=status,
            )
        )

    priority = {"СРОЧНО": 0, "КОНТРОЛЬ": 1}
    out.sort(key=lambda x: (priority.get(x.status, 9), -x.spent_pct, x.ingredient_name))

    return out
