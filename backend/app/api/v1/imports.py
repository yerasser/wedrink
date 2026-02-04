from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.imports import ImportResult
from app.services.excel_reader import read_xlsx_df
from app.services.imports import (
    import_ingredients,
    import_products,
    import_recipes,
    import_stock,
)

router = APIRouter()


@router.post("/ingredients", response_model=ImportResult)
async def upload_ingredients(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    df = read_xlsx_df(file)
    ins, upd, skp, errs = await import_ingredients(db, df)
    return {"inserted": ins, "updated": upd, "skipped": skp, "errors": errs}


@router.post("/products", response_model=ImportResult)
async def upload_products(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    df = read_xlsx_df(file)
    ins, upd, skp, errs = await import_products(db, df)
    return {"inserted": ins, "updated": upd, "skipped": skp, "errors": errs}


@router.post("/recipes", response_model=ImportResult)
async def upload_recipes(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    df = read_xlsx_df(file)
    ins, upd, skp, errs = await import_recipes(db, df)
    return {"inserted": ins, "updated": upd, "skipped": skp, "errors": errs}


@router.post("/stock", response_model=ImportResult)
async def upload_stock(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    df = read_xlsx_df(file)
    ins, upd, skp, errs = await import_stock(db, df)
    return {"inserted": ins, "updated": upd, "skipped": skp, "errors": errs}
