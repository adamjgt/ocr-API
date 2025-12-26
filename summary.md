Bangun **Backend OCR API production-ready** dengan spesifikasi berikut:

### **Tujuan**

Menyediakan OCR API yang:

* Stabil
* Scalable
* Aman
* Siap dipakai user nyata & dinilai HR backend engineer

---

## **Stack Wajib**

* **FastAPI** (web API)
* **Uvicorn** (ASGI server)
* **Tesseract OCR**
* **pdf2image + poppler-utils** (PDF → image)
* **Redis + RQ** (job queue)
* **Docker**
* **Railway deployment**
* **Loguru** (structured logging)
* **pytest** (testing)

---

## **Arsitektur Wajib**

* **Web Service** (FastAPI)
* **Worker Service** (RQ worker)
* **Redis** sebagai message broker
* OCR **tidak boleh synchronous**
* Semua OCR diproses di worker

---

## **Endpoint Wajib**

1. `POST /api/v1/ocr/submit`

   * Upload file (PNG/JPG/PDF)
   * Validasi size & type
   * Push job ke Redis
   * Return `job_id`

2. `GET /api/v1/ocr/result/{job_id}`

   * Return status: `queued | started | finished | failed`
   * Jika selesai → return text hasil OCR

3. `GET /api/v1/health`

   * Health check sederhana

---

## **OCR Processing Rules**

* PDF **HARUS** dikonversi ke image per halaman
* Max page limit (default: 20 halaman)
* Per-page OCR timeout (default: 10 detik)
* File size limit (default: 10 MB)
* Cleanup semua temp file
* Handle error:

  * PDF corrupt
  * PDF encrypted
  * Timeout
  * OCR failure

---

## **Job Queue**

* Gunakan **RQ**
* Worker menjalankan OCR function sync
* Simpan hasil di Redis
* `result_ttl` minimal 24 jam

---

## **Logging & Observability**

* Structured logging (request_id)
* Log:

  * request start / end
  * file type
  * page count
  * processing duration
* Tambahkan `X-Request-ID` header

---

## **Deployment (Railway)**

* 2 service:

  * Web: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT}`
  * Worker: `rq worker --url ${REDIS_URL} default`
* Tambahkan Redis add-on
* Semua config via environment variables

---

## **Docker Requirement**

* Install:

  * `tesseract-ocr`
  * `poppler-utils`
* Non-root container preferred
* Clean temp files

---

## **Testing Minimal**

* Unit test:

  * health endpoint
  * submit OCR job
* Integration test:

  * upload PNG
  * upload PDF
  * polling result

---

## **README (Wajib Profesional)**

* Problem statement
* Architecture diagram
* Design decision
* OCR flow
* Error handling strategy
* Scaling strategy
* How to deploy locally & on Railway

---

## **Standar Kualitas**

* Tidak ada OCR synchronous di request thread
* Tidak ada asumsi file = image
* Tidak ada blocking I/O di web layer
* Siap scale worker horizontal
* HR harus bisa melihat:
  **“ini backend engineer beneran, bukan script demo”**
