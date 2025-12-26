from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends
from loguru import logger

from app.api.v1.schemas import (
    OcrResponse,
    OcrSubmitResponse,
    OcrResultResponse,
    HealthResponse,
    DeveloperRegisterRequest,
    DeveloperRegisterResponse,
    DeveloperStatsResponse,
    ApiKeyRegenerateRequest,
    ApiKeyRegenerateResponse,
    ApiKeyRevokeRequest,
    ApiKeyRevokeResponse
)
from app.services.ocr_service import process_ocr_sync, save_upload_file_temp
from app.services.job_service import submit_ocr_job, get_job_result
from app.services import apikey_service
from app.utils.file_validator import validate_file, validate_file_size
from app.core.redis_client import redis_client
from app.core.middleware import get_request_id
from app.core.rate_limiter import limiter
from app.core.config import settings
from app.core.auth import require_api_key

router = APIRouter()


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns API status and Redis connection status.
    """
    redis_status = "connected" if redis_client.is_connected() else "disconnected"
    
    return HealthResponse(
        status="ok",
        redis=redis_status,
        version="1.0.0"
    )


# ============================================================================
# API Key Management (Self-Service)
# ============================================================================

@router.post("/auth/register", response_model=DeveloperRegisterResponse)
@limiter.limit("5/hour")
async def register_developer(request: Request, data: DeveloperRegisterRequest):
    """
    Register as a developer and get an API key.
    
    **Important:** The API key is only shown once! Save it securely.
    
    Rate limit: 5 registrations per hour per IP.
    """
    try:
        result = apikey_service.register_developer(
            email=data.email,
            name=data.name
        )
        logger.info(f"Developer registered | email={data.email}")
        return DeveloperRegisterResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed | email={data.email} error={e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.get("/auth/stats", response_model=DeveloperStatsResponse)
async def get_developer_stats(
    request: Request,
    api_key: str = Depends(require_api_key)
):
    """
    Get your API usage statistics.
    
    Requires a valid API key.
    """
    developer = apikey_service.get_developer_by_api_key(api_key)
    
    if not developer:
        raise HTTPException(status_code=404, detail="Developer not found")
    
    stats = apikey_service.get_developer_stats(developer["email"])
    return DeveloperStatsResponse(**stats)


@router.post("/auth/regenerate", response_model=ApiKeyRegenerateResponse)
@limiter.limit("3/day")
async def regenerate_api_key(request: Request, data: ApiKeyRegenerateRequest):
    """
    Regenerate your API key.
    
    **Warning:** This will invalidate your old API key immediately.
    
    Rate limit: 3 regenerations per day per IP.
    """
    try:
        result = apikey_service.regenerate_api_key(email=data.email)
        logger.info(f"API key regenerated | email={data.email}")
        return ApiKeyRegenerateResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Regeneration failed | email={data.email} error={e}")
        raise HTTPException(status_code=500, detail="Regeneration failed")


@router.post("/auth/revoke", response_model=ApiKeyRevokeResponse)
async def revoke_api_key(
    request: Request, 
    data: ApiKeyRevokeRequest,
    api_key: str = Depends(require_api_key)
):
    """
    Revoke/deactivate your API key.
    
    Requires a valid API key. After revocation, the key cannot be used.
    """
    # Verify the requester owns this email
    developer = apikey_service.get_developer_by_api_key(api_key)
    if not developer or developer["email"] != data.email:
        raise HTTPException(status_code=403, detail="Cannot revoke others' API keys")
    
    try:
        result = apikey_service.revoke_api_key(email=data.email)
        logger.info(f"API key revoked | email={data.email}")
        return ApiKeyRevokeResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Async OCR Endpoints (Production)
# ============================================================================

@router.post("/ocr/submit", response_model=OcrSubmitResponse)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW}")
async def submit_ocr(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Depends(require_api_key)
):
    """
    Submit a file for async OCR processing.
    
    - Validates file type and size
    - Pushes job to Redis queue
    - Returns job_id for polling
    
    Supported formats: PNG, JPG, JPEG, PDF
    Max file size: 10 MB
    Max PDF pages: 20
    """
    request_id = get_request_id(request)
    
    # Validate file type
    validate_file(file)
    
    # Read and validate file size
    content = await validate_file_size(file)
    
    logger.info(
        f"OCR submit | file={file.filename} size={len(content)} "
        f"request_id={request_id}"
    )
    
    # Submit job to queue
    try:
        job_id = submit_ocr_job(
            file_content=content,
            filename=file.filename,
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"Failed to submit job | error={e} request_id={request_id}")
        raise HTTPException(
            status_code=503,
            detail="Job queue unavailable. Please try again later."
        )
    
    return OcrSubmitResponse(job_id=job_id)


@router.get("/ocr/result/{job_id}", response_model=OcrResultResponse)
async def get_ocr_result(job_id: str):
    """
    Get the result of an OCR job.
    
    Poll this endpoint until status is 'finished' or 'failed'.
    
    Status values:
    - queued: Job is waiting in queue
    - started: Job is being processed
    - finished: OCR completed successfully
    - failed: OCR failed (see error field)
    """
    result = get_job_result(job_id)
    
    return OcrResultResponse(
        status=result["status"],
        text=result.get("text"),
        error=result.get("error")
    )


# ============================================================================
# Legacy Sync OCR Endpoint (Backward Compatibility)
# ============================================================================

@router.post("/ocr", response_model=OcrResponse, deprecated=True)
async def ocr_endpoint_sync(file: UploadFile = File(...)):
    """
    [DEPRECATED] Synchronous OCR endpoint.
    
    Use /ocr/submit and /ocr/result/{job_id} for production workloads.
    
    This endpoint processes OCR synchronously and may timeout for large files.
    """
    validate_file(file)
    content = await validate_file_size(file)
    
    try:
        # Save to temp file
        temp_path = save_upload_file_temp(content, file.filename)
        
        # Process synchronously
        result = process_ocr_sync(temp_path, file.filename)
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        
        return OcrResponse(text=result["text"])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
