"""
RQ Worker entry point.

Run with: python -m app.worker
Or: rq worker --url $REDIS_URL default (Linux/Mac only)

On Windows, use: python -m app.worker
"""
import os
import sys
import platform

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redis import Redis
from rq import Queue

from app.core.config import settings
from app.core.logging import setup_logging
from loguru import logger


def run_worker():
    """Start the RQ worker."""
    setup_logging()
    logger.info("Starting RQ Worker...")
    
    redis_conn = Redis.from_url(settings.REDIS_URL)
    queue = Queue("default", connection=redis_conn)
    
    # Use SimpleWorker on Windows (no fork support)
    # Use regular Worker on Linux/Mac
    if platform.system() == "Windows":
        from rq import SimpleWorker
        worker = SimpleWorker(
            queues=[queue],
            connection=redis_conn
        )
        logger.info(f"Using SimpleWorker (Windows mode) | redis={settings.REDIS_URL}")
    else:
        from rq import Worker
        worker = Worker(
            queues=[queue],
            connection=redis_conn
        )
        logger.info(f"Using Worker (Unix mode) | redis={settings.REDIS_URL}")
    
    logger.info(f"Worker listening on queue 'default'...")
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    run_worker()
