import sys
from loguru import logger
from app.core.config import settings


def setup_logging() -> None:
    """Configure Loguru for structured logging."""
    
    # Remove default handler
    logger.remove()
    
    # Log format with request_id support
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<yellow>{extra[request_id]}</yellow> | "
        "<level>{message}</level>"
    )
    
    # Simple format for when request_id is not available
    simple_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Add stdout handler
    logger.add(
        sys.stdout,
        format=simple_format,
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
        backtrace=True,
        diagnose=settings.DEBUG,
    )
    
    # Add file handler for production
    if settings.ENV == "production":
        logger.add(
            "logs/app.log",
            format=log_format.replace("<green>", "").replace("</green>", "")
                            .replace("<level>", "").replace("</level>", "")
                            .replace("<cyan>", "").replace("</cyan>", "")
                            .replace("<yellow>", "").replace("</yellow>", ""),
            level="INFO",
            rotation="100 MB",
            retention="7 days",
            compression="gz",
        )


def get_logger(request_id: str = "-"):
    """Get a logger instance with request_id context."""
    return logger.bind(request_id=request_id)
