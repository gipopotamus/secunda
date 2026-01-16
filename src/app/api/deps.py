from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthError
from app.core.settings import get_settings
from app.db.session import get_session
from app.repos.activities import ActivitiesRepo
from app.repos.buildings import BuildingsRepo
from app.repos.organizations import OrganizationsRepo
from app.services.activities import ActivitiesService
from app.services.buildings import BuildingsService
from app.services.organizations import OrganizationsService


async def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if x_api_key != get_settings().api_key:
        raise AuthError(message="Invalid API key", code="INVALID_API_KEY")


SessionDep = Depends(get_session)


def get_activities_repo(session: AsyncSession = SessionDep) -> ActivitiesRepo:
    return ActivitiesRepo(session)


def get_buildings_repo(session: AsyncSession = SessionDep) -> BuildingsRepo:
    return BuildingsRepo(session)


def get_organizations_repo(session: AsyncSession = SessionDep) -> OrganizationsRepo:
    return OrganizationsRepo(session)


def get_activities_service(repo: ActivitiesRepo = Depends(get_activities_repo)) -> ActivitiesService:
    return ActivitiesService(repo)


def get_organizations_service(
    orgs: OrganizationsRepo = Depends(get_organizations_repo),
    acts: ActivitiesRepo = Depends(get_activities_repo),
) -> OrganizationsService:
    return OrganizationsService(orgs=orgs, acts=acts)


def get_buildings_service(
    buildings: BuildingsRepo = Depends(get_buildings_repo),
    orgs: OrganizationsRepo = Depends(get_organizations_repo),
) -> BuildingsService:
    return BuildingsService(buildings=buildings, orgs=orgs)
