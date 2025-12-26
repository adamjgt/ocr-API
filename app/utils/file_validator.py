from fastapi import UploadFile, HTTPException
from app.core.config import settings


ALLOWED_EXTENSIONS = settings.ALLOWED_EXTENSIONS


def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file type and size.
    
    Raises:
        HTTPException: If file type or size is invalid
    """
    # Validate file type
    filename = file.filename.lower() if file.filename else ""
    ext = filename.split(".")[-1] if "." in filename else ""
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )


async def validate_file_size(file: UploadFile) -> bytes:
    """
    Read and validate file size.
    
    Returns:
        File content as bytes
    
    Raises:
        HTTPException: If file size exceeds limit
    """
    content = await file.read()
    
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds limit of {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    return content


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return filename.lower().split(".")[-1] if "." in filename else ""
