from rq.job import Job
from rq.exceptions import NoSuchJobError
from typing import Optional
from loguru import logger
from app.core.redis_client import redis_client
from app.core.config import settings
from app.services.ocr_service import process_ocr_sync, save_upload_file_temp


class JobStatus:
    QUEUED = "queued"
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"


def submit_ocr_job(file_content: bytes, filename: str, request_id: str = "-") -> str:
    """
    Submit an OCR job to the queue.
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        request_id: Request ID for tracing
    
    Returns:
        job_id: Unique identifier for the job
    """
    # Save file to temp location
    temp_path = save_upload_file_temp(file_content, filename)
    
    logger.info(
        f"Submitting OCR job | file={filename} request_id={request_id}"
    )
    
    # Enqueue the job
    job = redis_client.queue.enqueue(
        process_ocr_sync,
        temp_path,
        filename,
        result_ttl=settings.RESULT_TTL,
        job_timeout=settings.JOB_TIMEOUT,
        meta={
            "filename": filename,
            "request_id": request_id
        }
    )
    
    logger.info(f"Job submitted | job_id={job.id} file={filename}")
    return job.id


def get_job_result(job_id: str) -> dict:
    """
    Get the result of an OCR job.
    
    Args:
        job_id: The job identifier
    
    Returns:
        dict with status, text (if finished), and error (if failed)
    """
    try:
        job = Job.fetch(job_id, connection=redis_client.connection)
    except NoSuchJobError:
        return {
            "status": JobStatus.FAILED,
            "text": None,
            "error": "Job not found or expired"
        }
    
    # Map RQ job status to our status
    if job.is_queued:
        return {
            "status": JobStatus.QUEUED,
            "text": None,
            "error": None
        }
    elif job.is_started:
        return {
            "status": JobStatus.STARTED,
            "text": None,
            "error": None
        }
    elif job.is_finished:
        result = job.result
        if result and result.get("error"):
            return {
                "status": JobStatus.FAILED,
                "text": None,
                "error": result["error"]
            }
        return {
            "status": JobStatus.FINISHED,
            "text": result.get("text") if result else None,
            "error": None
        }
    elif job.is_failed:
        return {
            "status": JobStatus.FAILED,
            "text": None,
            "error": str(job.exc_info) if job.exc_info else "Job failed"
        }
    else:
        return {
            "status": JobStatus.QUEUED,
            "text": None,
            "error": None
        }


def get_job_info(job_id: str) -> Optional[dict]:
    """
    Get metadata about a job.
    
    Returns:
        dict with job metadata or None if not found
    """
    try:
        job = Job.fetch(job_id, connection=redis_client.connection)
        return {
            "id": job.id,
            "status": job.get_status(),
            "filename": job.meta.get("filename"),
            "request_id": job.meta.get("request_id"),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
        }
    except NoSuchJobError:
        return None
