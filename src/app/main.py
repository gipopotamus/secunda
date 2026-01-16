from __future__ import annotations

from fastapi import FastAPI

from app.api.error_handlers import install_error_handlers
from app.api.router import router as api_router
from app.core.settings import get_settings

settings = get_settings()

app = FastAPI(
    title="Organizations API",
    version="0.1.0",
    debug=settings.debug,
)

install_error_handlers(app)
app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
