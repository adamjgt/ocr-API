from fastapi.exception_handlers import http_exception_handler
from fastapi import HTTPException
from app.core.exceptions import http_error_handler, generic_error_handler
from fastapi import FastAPI
from app.api.v1.routes import router as v1_router

def create_app() -> FastAPI:
    app = FastAPI(title="OCR Processing API", version="1.0.0")

    # Routes
    app.include_router(v1_router, prefix="/api/v1")

    # Exception Handler
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    return app
app = create_app()
