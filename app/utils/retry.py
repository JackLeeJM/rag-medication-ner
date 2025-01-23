import logging
from functools import wraps
from qdrant_client.http.exceptions import UnexpectedResponse, ResponseHandlingException
from httpx import ConnectError, ReadTimeout, ConnectTimeout
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log,
)
from app.config.logging import get_logger


logger = get_logger(__name__)

QDRANT_HTTP_EXCEPTIONS = (
    ConnectionRefusedError,
    ResponseHandlingException,
    UnexpectedResponse,
    ConnectError,
    ConnectTimeout,
    ReadTimeout,
)


def retry_with_logging(func):
    @wraps(func)
    async def wrapper(args, **kwargs):
        try:
            return await func(args, **kwargs)
        except Exception as e:
            logger.error(f"Failed to {func.__name__}: {str(e)}")
            raise

    retry_decorator = retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(QDRANT_HTTP_EXCEPTIONS),
        before=before_log(logger, logging.INFO),
        after=after_log(logger, logging.INFO),
    )
    return retry_decorator(wrapper)
