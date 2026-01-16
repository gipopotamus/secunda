from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_organizations_service, verify_api_key
from app.schemas.common import ListResponse, Pagination
from app.schemas.organization import OrganizationCardOut, OrganizationGeoOut, OrganizationOut
from app.services.organizations import GeoQuery, OrganizationsService
from dataclasses import asdict

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("", response_model=ListResponse[OrganizationOut])
async def list_organizations(
    pg: Pagination = Depends(),
    svc: OrganizationsService = Depends(get_organizations_service),
    name: str = Query(min_length=1),
) -> ListResponse[OrganizationOut]:
    page = await svc.search_by_name(name=name, limit=pg.limit, offset=pg.offset)
    return ListResponse(
        total=page.total,
        items=[OrganizationOut(**asdict(o)) for o in page.items],
    )


@router.get("/by-activity/{activity_id}", response_model=ListResponse[OrganizationOut])
async def list_by_activity(
    activity_id: int,
    include_descendants: bool = Query(default=True),
    pg: Pagination = Depends(),
    svc: OrganizationsService = Depends(get_organizations_service),
) -> ListResponse[OrganizationOut]:
    page = await svc.list_by_activity(
        activity_id=activity_id,
        include_descendants=include_descendants,
        limit=pg.limit,
        offset=pg.offset,
    )
    return ListResponse(
        total=page.total,
        items=[OrganizationOut(**asdict(o)) for o in page.items],
    )


@router.get("/geo", response_model=ListResponse[OrganizationGeoOut])
async def geo_search(
    pg: Pagination = Depends(),
    svc: OrganizationsService = Depends(get_organizations_service),

    lat: float | None = Query(default=None, ge=-90, le=90),
    lon: float | None = Query(default=None, ge=-180, le=180),
    radius_m: float | None = Query(default=None, gt=0),

    min_lat: float | None = Query(default=None, ge=-90, le=90),
    min_lon: float | None = Query(default=None, ge=-180, le=180),
    max_lat: float | None = Query(default=None, ge=-90, le=90),
    max_lon: float | None = Query(default=None, ge=-180, le=180),
) -> ListResponse[OrganizationGeoOut]:
    page = await svc.geo_search(
        q=GeoQuery(
            lat=lat, lon=lon, radius_m=radius_m,
            min_lat=min_lat, min_lon=min_lon, max_lat=max_lat, max_lon=max_lon,
        ),
        limit=pg.limit,
        offset=pg.offset,
    )
    return ListResponse(
        total=page.total,
        items=[OrganizationGeoOut(**asdict(o)) for o in page.items],
    )




@router.get("/{org_id}", response_model=OrganizationCardOut)
async def get_organization_card(
    org_id: int,
    svc: OrganizationsService = Depends(get_organizations_service),
) -> OrganizationCardOut:
    row = await svc.get_card(org_id=org_id)
    return OrganizationCardOut(
        id=row.id,
        name=row.name,
        building_id=row.building_id,
        phones=row.phones,
        activities=row.activities,
    )