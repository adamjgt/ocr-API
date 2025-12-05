import pytesseract
from fastapi import UploadFile
import tempfile
import shutil

# ================================
# 1. SET TESSERACT BINARY PATH
# ================================
# Path default pada container Linux (Docker)
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# ================================
# 2. OCR LOGIC
# ================================
async def process_ocr(file: UploadFile) -> str:
    # Simpan file ke temporary
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    # Proses OCR
    text = pytesseract.image_to_string(tmp_path)

    return text.strip()
