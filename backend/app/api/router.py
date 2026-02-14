from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.me import router as me_router
from app.api.routes.ingredients import router as ingredients_router
from app.api.routes.products import router as products_router
from app.api.routes.recipes import router as recipes_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.receipts import router as receipts_router
from app.api.routes.receipt_items import router as receipt_items_router
from app.api.routes.reports import router as reports_router
from app.api.routes.users import router as users_router
from app.api.routes.apply import router as apply_router
from app.api.routes.rollback import router as rollback_router

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

router.include_router(auth_router)
router.include_router(me_router)
router.include_router(ingredients_router)
router.include_router(products_router)
router.include_router(recipes_router)
router.include_router(inventory_router)
router.include_router(receipts_router)
router.include_router(receipt_items_router)
router.include_router(apply_router)
router.include_router(rollback_router)
router.include_router(reports_router)
router.include_router(users_router)