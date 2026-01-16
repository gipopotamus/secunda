from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_activities_service, verify_api_key
from app.schemas.activity import ActivityNode, ActivityOut
from app.schemas.common import ListResponse, Pagination
from app.services.activities import ActivitiesService

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("", response_model=ListResponse[ActivityOut])
async def list_activities(
    pg: Pagination = Depends(),
    svc: ActivitiesService = Depends(get_activities_service),
    max_depth: int = Query(default=3, ge=1, le=3),
) -> ListResponse[ActivityOut]:
    page = await svc.list(limit=pg.limit, offset=pg.offset, max_depth=max_depth)
    return ListResponse(
        total=page.total,
        items=[ActivityOut(**asdict(a)) for a in page.items],
    )


@router.get("/tree", response_model=list[ActivityNode])
async def activities_tree(
    svc: ActivitiesService = Depends(get_activities_service),
    max_depth: int = Query(default=3, ge=1, le=3),
) -> list[ActivityNode]:
    tree = await svc.tree(max_depth=max_depth)

    def map_node(n) -> ActivityNode:
        return ActivityNode(
            id=n.id,
            name=n.name,
            parent_id=n.parent_id,
            depth=n.depth,
            children=[map_node(c) for c in n.children],
        )

    return [map_node(n) for n in tree]
