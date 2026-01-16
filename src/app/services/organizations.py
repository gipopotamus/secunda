from __future__ import annotations

from dataclasses import dataclass

from app.core.errors import NotFoundError, ValidationError
from app.repos.activities import ActivitiesRepo
from app.repos.dto import OrganizationCardRow, OrganizationGeoRow, OrganizationRow, Page
from app.repos.organizations import OrganizationsRepo


@dataclass(slots=True, frozen=True)
class GeoQuery:
    # radius mode
    lat: float | None = None
    lon: float | None = None
    radius_m: float | None = None
    # bbox mode
    min_lat: float | None = None
    min_lon: float | None = None
    max_lat: float | None = None
    max_lon: float | None = None


class OrganizationsService:
    def __init__(self, orgs: OrganizationsRepo, acts: ActivitiesRepo) -> None:
        self.orgs = orgs
        self.acts = acts

    async def get_card(self, *, org_id: int) -> OrganizationCardRow:
        row = await self.orgs.get_card(org_id=org_id)
        if row is None:
            raise NotFoundError(message="Organization not found", code="ORG_NOT_FOUND")
        return row

    async def search_by_name(self, *, name: str, limit: int, offset: int) -> Page[OrganizationRow]:
        return await self.orgs.search_by_name(name=name, limit=limit, offset=offset)

    async def list_by_activity(
        self,
        *,
        activity_id: int,
        include_descendants: bool,
        limit: int,
        offset: int,
    ) -> Page[OrganizationRow]:
        ids = (
            await self.acts.subtree_ids(root_id=activity_id, max_depth=3)
            if include_descendants
            else [activity_id]
        )
        return await self.orgs.list_by_activity_ids(activity_ids=ids, limit=limit, offset=offset)

    async def geo_search(self, *, q: GeoQuery, limit: int, offset: int) -> Page[OrganizationGeoRow]:
        radius_mode = q.lat is not None and q.lon is not None and q.radius_m is not None
        bbox_mode = None not in (q.min_lat, q.min_lon, q.max_lat, q.max_lon)

        if radius_mode == bbox_mode:
            raise ValidationError(
                message="Specify either (lat, lon, radius_m) or (min_lat, min_lon, max_lat, max_lon)",
                code="GEO_PARAMS_INVALID",
            )

        if radius_mode:
            return await self.orgs.geo_search_radius(
                lat=float(q.lat),
                lon=float(q.lon),
                radius_m=float(q.radius_m),
                limit=limit,
                offset=offset,
            )

        return await self.orgs.geo_search_bbox(
            min_lat=float(q.min_lat),
            min_lon=float(q.min_lon),
            max_lat=float(q.max_lat),
            max_lon=float(q.max_lon),
            limit=limit,
            offset=offset,
        )
