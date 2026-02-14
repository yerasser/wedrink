from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exc_handler(_: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            return JSONResponse(status_code=exc.status_code, content=detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "http_error", "message": str(detail)},
        )

    @app.exception_handler(HTTPException)
    async def fastapi_http_exc_handler(_: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            return JSONResponse(status_code=exc.status_code, content=detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "http_error", "message": str(detail)},
        )

    @app.exception_handler(Exception)
    async def unhandled_exc_handler(_: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"error": "internal_error", "message": str(exc)})
