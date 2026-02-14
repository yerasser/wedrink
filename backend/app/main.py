from fastapi import FastAPI

from app.core.config import settings
from app.core.errors import install_error_handlers
from app.api.router import router as api_router

app = FastAPI(title="WeDrinkStorage API")
@app.on_event("startup")
async def startup():
    print("STARTUP OK", flush=True)
install_error_handlers(app)
app.include_router(api_router, prefix="/api")
print(1)
