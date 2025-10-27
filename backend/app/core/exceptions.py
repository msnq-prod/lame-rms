from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

import structlog

logger = structlog.get_logger(__name__)


class ApplicationError(RuntimeError):
    """Base exception for expected application errors."""

    def __init__(self, message: str, *, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for the FastAPI app."""

    @app.exception_handler(ApplicationError)  # type: ignore[misc]
    async def handle_application_error(request: Request, exc: ApplicationError) -> JSONResponse:
        logger.warning("application_error", path=request.url.path, detail=exc.message)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)  # type: ignore[misc]
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unexpected_error", path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )


__all__ = ["ApplicationError", "register_exception_handlers"]
