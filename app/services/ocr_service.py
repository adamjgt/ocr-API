import pytesseract
from fastapi import UploadFile
import tempfile
import shutil
from pdf2image import convert_from_path
import os

async def process_ocr(file: UploadFile) -> str:
    # Simpan file ke temporary
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    if file.filename.lower().endswith(".pdf"):
        # Convert PDF ke images
        images = convert_from_path(tmp_path)
        text = []

        for img in images:
            text.append(pytesseract.image_to_string(img))

        os.remove(tmp_path)
        return "\n".join(text).strip()

    else:
        # Image langsung
        text = pytesseract.image_to_string(tmp_path)
        os.remove(tmp_path)
        return text.strip()
