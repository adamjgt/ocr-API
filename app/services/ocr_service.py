import pytesseract
import tempfile
import shutil
import os
import signal
from pathlib import Path
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError
from loguru import logger
from app.core.config import settings


class OCRTimeoutError(Exception):
    """Raised when OCR processing times out."""
    pass


class PDFProcessingError(Exception):
    """Raised when PDF cannot be processed."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for OCR timeout."""
    raise OCRTimeoutError("OCR processing timed out")


def process_ocr_sync(file_path: str, filename: str) -> dict:
    """
    Process OCR synchronously (to be run by RQ worker).
    
    Args:
        file_path: Path to the temporary file
        filename: Original filename for type detection
    
    Returns:
        dict with 'text' or 'error' key
    """
    temp_files = [file_path]
    
    try:
        logger.info(f"Starting OCR processing | file={filename}")
        
        if filename.lower().endswith(".pdf"):
            result = _process_pdf(file_path, temp_files)
        else:
            result = _process_image(file_path)
        
        logger.info(f"OCR completed successfully | file={filename} chars={len(result)}")
        return {"text": result, "error": None}
        
    except OCRTimeoutError as e:
        logger.error(f"OCR timeout | file={filename} error={str(e)}")
        return {"text": None, "error": f"OCR processing timed out"}
        
    except PDFProcessingError as e:
        logger.error(f"PDF processing error | file={filename} error={str(e)}")
        return {"text": None, "error": str(e)}
        
    except Exception as e:
        logger.error(f"OCR failed | file={filename} error={str(e)}")
        return {"text": None, "error": f"OCR processing failed: {str(e)}"}
        
    finally:
        # Cleanup all temp files
        _cleanup_temp_files(temp_files)


def _process_pdf(file_path: str, temp_files: list) -> str:
    """Process PDF file page by page."""
    try:
        # Try to get page count first
        images = convert_from_path(file_path, first_page=1, last_page=1)
        
        # Convert all pages up to limit
        images = convert_from_path(
            file_path,
            first_page=1,
            last_page=settings.MAX_PDF_PAGES
        )
        
        page_count = len(images)
        logger.info(f"PDF converted | pages={page_count}")
        
        if page_count == 0:
            raise PDFProcessingError("PDF has no pages or is empty")
        
        texts = []
        for i, img in enumerate(images, 1):
            # Save image temporarily for processing
            img_path = tempfile.mktemp(suffix=".png")
            temp_files.append(img_path)
            img.save(img_path, "PNG")
            
            # Process with timeout
            try:
                text = _ocr_with_timeout(img_path, settings.OCR_TIMEOUT_PER_PAGE)
                texts.append(f"--- Page {i} ---\n{text}")
                logger.debug(f"Page {i}/{page_count} processed")
            except OCRTimeoutError:
                texts.append(f"--- Page {i} ---\n[TIMEOUT: Page processing exceeded {settings.OCR_TIMEOUT_PER_PAGE}s]")
                logger.warning(f"Page {i} timed out")
        
        return "\n\n".join(texts).strip()
        
    except PDFPageCountError:
        raise PDFProcessingError("PDF is corrupted or has invalid page count")
    except PDFSyntaxError:
        raise PDFProcessingError("PDF has syntax errors or is corrupted")
    except Exception as e:
        if "password" in str(e).lower() or "encrypted" in str(e).lower():
            raise PDFProcessingError("PDF is encrypted and cannot be processed")
        raise


def _process_image(file_path: str) -> str:
    """Process single image file."""
    return _ocr_with_timeout(file_path, settings.OCR_TIMEOUT_PER_PAGE)


def _ocr_with_timeout(file_path: str, timeout_seconds: int) -> str:
    """Run OCR with timeout (Unix-only for signal, fallback for Windows)."""
    try:
        # Windows doesn't support SIGALRM, use simple approach
        if os.name == 'nt':
            return pytesseract.image_to_string(file_path)
        
        # Unix: use signal for timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            result = pytesseract.image_to_string(file_path)
            signal.alarm(0)  # Cancel alarm
            return result
        finally:
            signal.signal(signal.SIGALRM, old_handler)
            
    except OCRTimeoutError:
        raise
    except Exception as e:
        raise Exception(f"OCR engine error: {str(e)}")


def _cleanup_temp_files(file_paths: list) -> None:
    """Clean up temporary files safely."""
    for path in file_paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
                logger.debug(f"Cleaned up temp file: {path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {path}: {e}")


def save_upload_file_temp(content: bytes, filename: str) -> str:
    """
    Save uploaded file content to a temporary file.
    
    Returns:
        Path to the temporary file
    """
    suffix = Path(filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        return tmp.name
