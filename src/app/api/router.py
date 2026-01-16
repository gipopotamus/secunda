from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.activities import router as activities_router
from app.api.v1.buildings import router as buildings_router
from app.api.v1.organizations import router as organizations_router

router = APIRouter(prefix="/api/v1")

router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
router.include_router(buildings_router, prefix="/buildings", tags=["buildings"])
router.include_router(activities_router, prefix="/activities", tags=["activities"])
