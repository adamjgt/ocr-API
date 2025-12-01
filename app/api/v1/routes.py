from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ocr_service import process_ocr
from app.utils.file_validator import validate_file
from app.api.v1.schemas import OcrResponse

router = APIRouter()

@router.post("/ocr", response_model=OcrResponse)
async def ocr_endpoint(file: UploadFile = File(...)):
    validate_file(file)

    try:
        text = await process_ocr(file)
        return OcrResponse(text=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health_check():
    return {"status": "ok"}
