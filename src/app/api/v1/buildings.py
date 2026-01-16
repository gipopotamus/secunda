from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.api.deps import get_buildings_service, verify_api_key
from app.schemas.building import BuildingOut
from app.schemas.common import ListResponse, Pagination
from app.schemas.organization import OrganizationOut
from app.services.buildings import BuildingsService

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("", response_model=ListResponse[BuildingOut])
async def list_buildings(
    pg: Pagination = Depends(),
    svc: BuildingsService = Depends(get_buildings_service),
) -> ListResponse[BuildingOut]:
    page = await svc.list(limit=pg.limit, offset=pg.offset)
    return ListResponse(
        total=page.total,
        items=[BuildingOut(**asdict(b)) for b in page.items],
    )


@router.get("/{building_id}/organizations", response_model=ListResponse[OrganizationOut])
async def list_building_orgs(
    building_id: int,
    pg: Pagination = Depends(),
    svc: BuildingsService = Depends(get_buildings_service),
) -> ListResponse[OrganizationOut]:
    page = await svc.organizations(building_id=building_id, limit=pg.limit, offset=pg.offset)
    return ListResponse(
        total=page.total,
        items=[OrganizationOut(**asdict(o)) for o in page.items],
    )
