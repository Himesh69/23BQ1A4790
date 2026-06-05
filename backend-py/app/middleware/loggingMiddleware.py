import uuid
from time import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.logger import get_logger
from src.types import LogContextOptions


class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        logger = get_logger()
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        start_time = time()

        logger.push_context(LogContextOptions(
            requestId=request_id,
            additionalContext={
                "method": request.method,
                "path": request.url.path,
            }
        ))

        try:
            await logger.info(
                "middleware",
                f"Incoming {request.method} request to {request.url.path}",
                {
                    "additionalContext": {
                        "method": request.method,
                        "path": request.url.path,
                    }
                }
            )

            response = await call_next(request)

            duration_ms = (time() - start_time) * 1000
            status_code = response.status_code

            if status_code >= 400:
                await logger.warn(
                    "middleware",
                    f"Response with status {status_code}",
                    {
                        "additionalContext": {
                            "duration_ms": f"{duration_ms:.2f}",
                            "statusCode": status_code
                        }
                    }
                )
            else:
                await logger.info(
                    "middleware",
                    "Request completed successfully",
                    {
                        "additionalContext": {
                            "duration_ms": f"{duration_ms:.2f}",
                            "statusCode": status_code
                        }
                    }
                )

            return response

        finally:
            logger.pop_context()
