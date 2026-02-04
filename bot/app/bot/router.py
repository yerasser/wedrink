from aiogram import Router
from .handlers.start import router as start_router
from .handlers.receipt_upload import router as upload_router
from .handlers.alerts import router as alerts_router

def build_router() -> Router:
    r = Router()
    r.include_router(start_router)
    r.include_router(upload_router)
    r.include_router(alerts_router)
    return r
