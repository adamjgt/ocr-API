# OCR Processing API

## Deskripsi
API untuk memproses file image/PDF dan mengekstrak teks menggunakan OCR.

## Fitur
- Upload file: PNG, JPG, JPEG, PDF
- Validasi file
- Machine-readable OCR endpoint
- Global error handler
- FastAPI auto documentation

## Endpoint
POST /api/v1/ocr

**Request:**
- multipart/form-data
- file: UploadFile

**Response:**
{
  "text": "hasil ocr..."
}

## Cara Menjalankan
pip install -r requirements.txt
uvicorn app.main:app --reload
