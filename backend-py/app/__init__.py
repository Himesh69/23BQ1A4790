import sys
import os
from datetime import datetime

# add logging middleware package to path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../packages/logging-middleware-py")
)

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.logger import create_logger, get_logger
from src.types import LoggerConfig, LogContextOptions
from app.config import settings
from app.middleware import LoggingMiddleware
from app.routes import user_router
from app.repository import db_service
from app.tasks import task_service
from app.models import HealthResponse


# init logger
logger_config = LoggerConfig(
    apiEndpoint=settings.LOG_API_ENDPOINT,
    stack="backend",
    apiKey=settings.LOG_API_KEY,
    batchSize=settings.LOG_BATCH_SIZE,
    flushInterval=settings.LOG_FLUSH_INTERVAL,
    enableConsoleOutput=True,
)

logger = create_logger(logger_config)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.add_middleware(LoggingMiddleware)
app.include_router(user_router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    app_logger = get_logger()
    await app_logger.debug("route", "Health check endpoint accessed")
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.on_event("startup")
async def startup_event():
    app_logger = get_logger()

    try:
        await app_logger.info(
            "controller",
            "Application startup initiated",
            {
                "additionalContext": {
                    "nodeEnv": settings.DEBUG and "development" or "production",
                    "port": settings.PORT,
                }
            }
        )

        await db_service.connect()

        await task_service.start_cleanup_job()
        await task_service.start_health_check_job()

        await app_logger.info(
            "controller",
            f"Server running on port {settings.PORT}",
            {
                "additionalContext": {
                    "url": f"http://localhost:{settings.PORT}",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            }
        )

    except Exception as e:
        await app_logger.fatal(
            "controller",
            f"Failed to start application: {str(e)}"
        )
        raise


@app.on_event("shutdown")
async def shutdown_event():
    app_logger = get_logger()

    try:
        await app_logger.info("controller", "Application shutdown initiated")
        await task_service.stop_all_jobs()
        await db_service.disconnect()
        await app_logger.force_flush()
        await app_logger.info("controller", "Application shutdown completed")

    except Exception as e:
        print(f"Error during shutdown: {str(e)}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    app_logger = get_logger()

    await app_logger.warn(
        "middleware",
        f"HTTP exception: {exc.detail}",
        {
            "additionalContext": {
                "status_code": exc.status_code,
                "path": request.url.path,
            }
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    app_logger = get_logger()

    await app_logger.error(
        "middleware",
        f"Unhandled error: {str(exc)}",
        {
            "additionalContext": {
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
            }
        }
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/{full_path:path}")
async def not_found(full_path: str):
    app_logger = get_logger()

    await app_logger.warn(
        "route",
        f"Route not found: GET /{full_path}",
    )

    raise HTTPException(status_code=404, detail="Not Found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
    )
