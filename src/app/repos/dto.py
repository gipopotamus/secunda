from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Page(Generic[T]):
    total: int
    items: list[T]


@dataclass(frozen=True, slots=True)
class BuildingRow:
    id: int
    address: str
    lat: float
    lon: float


@dataclass(frozen=True, slots=True)
class ActivityRow:
    id: int
    name: str
    parent_id: int | None
    depth: int


@dataclass(frozen=True, slots=True)
class OrganizationRow:
    id: int
    name: str
    building_id: int


@dataclass(frozen=True, slots=True)
class OrganizationGeoRow(OrganizationRow):
    distance_m: float | None


@dataclass(frozen=True, slots=True)
class OrganizationCardRow:
    id: int
    name: str
    building_id: int
    phones: list[str]
    activities: list[str]
