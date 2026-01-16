from __future__ import annotations

from pydantic import BaseModel, Field


class BuildingOut(BaseModel):
    id: int
    address: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
