from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AppError(Exception):
    """
    Base domain/application error.

    Services should raise only AppError (or subclasses), never FastAPI/HTTP-specific exceptions.
    """

    message: str
    code: str = "APP_ERROR"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.code}: {self.message}"


@dataclass(slots=True)
class NotFoundError(AppError):
    code: str = "NOT_FOUND"


@dataclass(slots=True)
class ValidationError(AppError):
    code: str = "VALIDATION_ERROR"


@dataclass(slots=True)
class AuthError(AppError):
    code: str = "AUTH_ERROR"
