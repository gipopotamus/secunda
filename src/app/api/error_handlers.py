from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import AppError, AuthError, NotFoundError, ValidationError
from app.schemas.errors import ProblemDetails


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        status = _map_status(exc)
        problem = ProblemDetails(
            title=_map_title(exc),
            status=status,
            detail=exc.message,
            instance=str(request.url.path),
            code=exc.code,
        )
        return JSONResponse(status_code=status, content=problem.model_dump())

    def _map_status(exc: AppError) -> int:
        if isinstance(exc, AuthError):
            return 401
        if isinstance(exc, NotFoundError):
            return 404
        if isinstance(exc, ValidationError):
            return 400
        return 500

    def _map_title(exc: AppError) -> str:
        if isinstance(exc, AuthError):
            return "Unauthorized"
        if isinstance(exc, NotFoundError):
            return "Not Found"
        if isinstance(exc, ValidationError):
            return "Bad Request"
        return "Internal Server Error"
