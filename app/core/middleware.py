import uuid
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add X-Request-ID header to all requests."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get existing request ID or generate new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Store in request state for access in handlers
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request/response details."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get request ID from state (set by RequestIDMiddleware)
        request_id = getattr(request.state, "request_id", "-")
        
        # Log request start
        start_time = time.time()
        logger.info(
            f"Request started | method={request.method} path={request.url.path} "
            f"request_id={request_id}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        duration_ms = round(duration * 1000, 2)
        
        # Log request end
        logger.info(
            f"Request completed | method={request.method} path={request.url.path} "
            f"status={response.status_code} duration={duration_ms}ms "
            f"request_id={request_id}"
        )
        
        return response


def get_request_id(request: Request) -> str:
    """Helper to get request ID from request state."""
    return getattr(request.state, "request_id", "-")
