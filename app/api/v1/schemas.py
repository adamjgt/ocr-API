from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class OcrResponse(BaseModel):
    """Response for legacy synchronous OCR endpoint."""
    text: str


class OcrSubmitResponse(BaseModel):
    """Response for async OCR job submission."""
    job_id: str
    message: str = "Job submitted successfully"


class OcrResultResponse(BaseModel):
    """Response for OCR job result polling."""
    status: str  # queued | started | finished | failed
    text: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response for health check endpoint."""
    status: str
    redis: Optional[str] = None
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None


# ============================================================================
# API Key Management Schemas
# ============================================================================

class DeveloperRegisterRequest(BaseModel):
    """Request to register a new developer."""
    email: EmailStr = Field(..., description="Developer's email address")
    name: str = Field(..., min_length=2, max_length=100, description="Developer's name")


class DeveloperRegisterResponse(BaseModel):
    """Response after successful registration."""
    email: str
    name: str
    api_key: str = Field(..., description="Your API key. Save it securely!")
    created_at: str
    message: str


class DeveloperStatsResponse(BaseModel):
    """Developer usage statistics."""
    email: str
    name: str
    created_at: str
    last_used_at: Optional[str] = None
    request_count: int = 0
    is_active: bool = True


class ApiKeyRegenerateRequest(BaseModel):
    """Request to regenerate API key."""
    email: EmailStr = Field(..., description="Developer's email address")


class ApiKeyRegenerateResponse(BaseModel):
    """Response after API key regeneration."""
    email: str
    api_key: str = Field(..., description="Your new API key")
    regenerated_at: str
    message: str


class ApiKeyRevokeRequest(BaseModel):
    """Request to revoke API key."""
    email: EmailStr = Field(..., description="Developer's email address")


class ApiKeyRevokeResponse(BaseModel):
    """Response after API key revocation."""
    email: str
    is_active: bool
    revoked_at: str
    message: str
