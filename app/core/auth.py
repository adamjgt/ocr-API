from fastapi import HTTPException, Security, Request
from fastapi.security import APIKeyHeader
from typing import Optional
from app.core.config import settings


# API Key header definition
api_key_header = APIKeyHeader(
    name=settings.API_KEY_HEADER,
    auto_error=False,
    description="API Key for authentication"
)


def validate_api_key_from_redis(api_key: str) -> bool:
    """
    Validate API key against Redis-stored developer keys.
    
    Returns True if key is valid and active.
    """
    try:
        from app.services import apikey_service
        return apikey_service.validate_api_key(api_key)
    except Exception:
        return False


class APIKeyAuth:
    """API Key authentication dependency."""
    
    def __init__(self, required: bool = True):
        """
        Initialize API Key auth.
        
        Args:
            required: If True, raises 401 when key is missing/invalid.
                     If False, allows unauthenticated access (for optional auth).
        """
        self.required = required
    
    async def __call__(
        self,
        request: Request,
        api_key: Optional[str] = Security(api_key_header)
    ) -> Optional[str]:
        """
        Validate API key from request header.
        
        Checks both:
        1. Static API keys from environment (API_KEYS setting)
        2. Dynamic API keys registered in Redis
        
        Returns:
            The API key if valid, None if auth is disabled or optional.
        
        Raises:
            HTTPException: 401 if key is missing or invalid (when required).
        """
        # Skip auth if disabled globally
        if not settings.API_KEY_ENABLED:
            return None
        
        # Check if API key is provided
        if not api_key:
            # Allow if no static keys AND we're not requiring dynamic keys
            if not settings.api_keys_list and not self.required:
                return None
            
            if self.required:
                raise HTTPException(
                    status_code=401,
                    detail="API key is missing",
                    headers={"WWW-Authenticate": "ApiKey"}
                )
            return None
        
        # Check 1: Static API keys from environment
        if settings.api_keys_list and api_key in settings.api_keys_list:
            request.state.api_key = api_key[:8] + "..."
            return api_key
        
        # Check 2: Dynamic API keys from Redis
        if validate_api_key_from_redis(api_key):
            request.state.api_key = api_key[:8] + "..."
            return api_key
        
        # If we get here, the key is invalid
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )


# Pre-configured dependencies
require_api_key = APIKeyAuth(required=True)
optional_api_key = APIKeyAuth(required=False)
