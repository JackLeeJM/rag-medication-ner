import sys
import logging
from pathlib import Path
from loguru import logger

# Remove default logger
logger.remove()

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configure loguru logger
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
    colorize=True,
)

# Add file logging with rotation
logger.add(
    LOG_DIR / "app_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # Create new file at midnight
    retention="30 days",  # Keep logs for 30 days
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    compression="zip",  # Compress rotated files
)


# Intercept standard library logging
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# Configure intercept handler for standard library logging
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# Configure uvicorn logging
logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]


def get_logger(name: str):
    """Get a logger instance with the specified name"""
    return logger.bind(context=name)
