from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from loguru import logger

from app.core.exceptions import http_error_handler, generic_error_handler
from app.core.middleware import RequestIDMiddleware, LoggingMiddleware
from app.core.logging import setup_logging
from app.core.redis_client import redis_client
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler
from app.api.v1.routes import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    setup_logging()
    logger.info("Starting OCR Processing API...")
    
    try:
        redis_client.connect()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis not available: {e}. Async OCR will not work.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down OCR Processing API...")
    redis_client.disconnect()


def create_app() -> FastAPI:
    app = FastAPI(
        title="OCR Processing API",
        version="1.0.0",
        description="Production-ready OCR API with async job queue processing",
        lifespan=lifespan
    )

    # Rate Limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # Middleware (order matters - RequestID first, then Logging)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Routes
    app.include_router(v1_router, prefix="/api/v1")

    # Exception Handler
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    return app


app = create_app()
