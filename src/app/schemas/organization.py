from __future__ import annotations

from pydantic import BaseModel, Field


class OrganizationOut(BaseModel):
    id: int
    name: str
    building_id: int


class OrganizationCardOut(BaseModel):
    id: int
    name: str
    building_id: int
    phones: list[str]
    activities: list[str]


class OrganizationGeoOut(OrganizationOut):
    distance_m: float | None = Field(default=None, ge=0)
