from fastapi import APIRouter
from app.api.v1.receipts import router as receipts_router
from app.api.v1.imports import router as imports_router
from app.api.v1.stock import router as stock_router
from app.api.v1.ocr import router as ocr_router

api_router = APIRouter()
api_router.include_router(receipts_router, prefix="/api/v1/receipts", tags=["receipts"])
api_router.include_router(ocr_router, prefix="/api/v1/ocr", tags=["ocr"])
api_router.include_router(imports_router, prefix="/api/v1/import", tags=["import"])
api_router.include_router(stock_router, prefix="/api/v1/stock", tags=["stock"])

