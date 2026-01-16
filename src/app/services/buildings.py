from __future__ import annotations

from app.repos.buildings import BuildingsRepo
from app.repos.dto import BuildingRow, OrganizationRow, Page
from app.repos.organizations import OrganizationsRepo


class BuildingsService:
    def __init__(self, buildings: BuildingsRepo, orgs: OrganizationsRepo) -> None:
        self.buildings = buildings
        self.orgs = orgs

    async def list(self, *, limit: int, offset: int) -> Page[BuildingRow]:
        return await self.buildings.list(limit=limit, offset=offset)

    async def organizations(self, *, building_id: int, limit: int, offset: int) -> Page[OrganizationRow]:
        return await self.orgs.list_by_building(building_id=building_id, limit=limit, offset=offset)
