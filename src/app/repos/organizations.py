from __future__ import annotations

from collections.abc import Sequence

from geoalchemy2 import Geography, Geometry
from sqlalchemy import cast, distinct, func, select
from sqlalchemy.dialects import postgresql

from app.models.activity import Activity
from app.models.building import Building
from app.models.organization import Organization, OrganizationPhone, organization_activities
from app.repos.base import Repo
from app.repos.dto import OrganizationCardRow, OrganizationGeoRow, OrganizationRow, Page


class OrganizationsRepo(Repo):
    async def get_card(self, *, org_id: int) -> OrganizationCardRow | None:
        phones_agg = func.array_remove(func.array_agg(distinct(OrganizationPhone.phone)), None)
        acts_agg = func.array_remove(func.array_agg(distinct(Activity.name)), None)

        empty_text_array = cast(
            postgresql.array([], type_=postgresql.TEXT),
            postgresql.ARRAY(postgresql.TEXT),
        )

        stmt = (
            select(
                Organization.id.label("id"),
                Organization.name.label("name"),
                Organization.building_id.label("building_id"),
                func.coalesce(phones_agg, empty_text_array).label("phones"),
                func.coalesce(acts_agg, empty_text_array).label("activities"),
            )
            .outerjoin(OrganizationPhone, OrganizationPhone.organization_id == Organization.id)
            .outerjoin(organization_activities, organization_activities.c.organization_id == Organization.id)
            .outerjoin(Activity, Activity.id == organization_activities.c.activity_id)
            .where(Organization.id == org_id)
            .group_by(Organization.id, Organization.name, Organization.building_id)
        )

        row = (await self.session.execute(stmt)).one_or_none()
        if row is None:
            return None

        phones = [str(x) for x in (row.phones or [])]
        activities = [str(x) for x in (row.activities or [])]
        return OrganizationCardRow(
            id=int(row.id),
            name=str(row.name),
            building_id=int(row.building_id),
            phones=phones,
            activities=activities,
        )

    async def search_by_name(self, *, name: str, limit: int, offset: int) -> Page[OrganizationRow]:
        pattern = f"%{name}%"
        where = Organization.name.ilike(pattern)

        total_stmt = select(func.count()).select_from(select(Organization.id).where(where).subquery())
        total = int(await self.session.scalar(total_stmt) or 0)

        stmt = (
            select(Organization.id, Organization.name, Organization.building_id)
            .where(where)
            .order_by(func.similarity(Organization.name, name).desc(), Organization.id.asc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.session.execute(stmt)).all()
        items = [OrganizationRow(id=int(r.id), name=str(r.name), building_id=int(r.building_id)) for r in rows]
        return Page(total=total, items=items)

    async def list_by_building(self, *, building_id: int, limit: int, offset: int) -> Page[OrganizationRow]:
        where = Organization.building_id == building_id

        total_stmt = select(func.count()).select_from(select(Organization.id).where(where).subquery())
        total = int(await self.session.scalar(total_stmt) or 0)

        stmt = (
            select(Organization.id, Organization.name, Organization.building_id)
            .where(where)
            .order_by(Organization.id.asc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.session.execute(stmt)).all()
        items = [OrganizationRow(id=int(r.id), name=str(r.name), building_id=int(r.building_id)) for r in rows]
        return Page(total=total, items=items)

    async def list_by_activity_ids(
        self,
        *,
        activity_ids: Sequence[int],
        limit: int,
        offset: int,
    ) -> Page[OrganizationRow]:
        if not activity_ids:
            return Page(total=0, items=[])

        org_ids_subq = (
            select(distinct(Organization.id).label("id"))
            .join(organization_activities, organization_activities.c.organization_id == Organization.id)
            .where(organization_activities.c.activity_id.in_(list(activity_ids)))
            .subquery()
        )

        total_stmt = select(func.count()).select_from(org_ids_subq)
        total = int(await self.session.scalar(total_stmt) or 0)

        stmt = (
            select(Organization.id, Organization.name, Organization.building_id)
            .join(org_ids_subq, org_ids_subq.c.id == Organization.id)
            .order_by(Organization.id.asc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.session.execute(stmt)).all()
        items = [OrganizationRow(id=int(r.id), name=str(r.name), building_id=int(r.building_id)) for r in rows]
        return Page(total=total, items=items)

    async def geo_search_radius(
        self,
        *,
        lat: float,
        lon: float,
        radius_m: float,
        limit: int,
        offset: int,
    ) -> Page[OrganizationGeoRow]:
        point = cast(
            func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
            Geography(geometry_type="POINT", srid=4326),
        )

        where = func.ST_DWithin(Building.geom, point, radius_m)

        base = (
            select(
                Organization.id.label("id"),
                Organization.name.label("name"),
                Organization.building_id.label("building_id"),
                func.ST_Distance(Building.geom, point).label("distance_m"),
            )
            .join(Building, Building.id == Organization.building_id)
            .where(where)
            .subquery()
        )

        total_stmt = select(func.count()).select_from(select(base.c.id).subquery())
        total = int(await self.session.scalar(total_stmt) or 0)

        stmt = (
            select(base.c.id, base.c.name, base.c.building_id, base.c.distance_m)
            .order_by(base.c.distance_m.asc(), base.c.id.asc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.session.execute(stmt)).all()
        items = [
            OrganizationGeoRow(
                id=int(r.id),
                name=str(r.name),
                building_id=int(r.building_id),
                distance_m=float(r.distance_m),
            )
            for r in rows
        ]
        return Page(total=total, items=items)

    async def geo_search_bbox(
        self,
        *,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        limit: int,
        offset: int,
    ) -> Page[OrganizationGeoRow]:
        envelope = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        geom_as_geom = cast(Building.geom, Geometry(geometry_type="POINT", srid=4326))
        where = func.ST_Intersects(geom_as_geom, envelope)

        base = (
            select(
                Organization.id.label("id"),
                Organization.name.label("name"),
                Organization.building_id.label("building_id"),
            )
            .join(Building, Building.id == Organization.building_id)
            .where(where)
            .subquery()
        )

        total_stmt = select(func.count()).select_from(select(base.c.id).subquery())
        total = int(await self.session.scalar(total_stmt) or 0)

        stmt = (
            select(base.c.id, base.c.name, base.c.building_id)
            .order_by(base.c.id.asc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.session.execute(stmt)).all()
        items = [
            OrganizationGeoRow(
                id=int(r.id),
                name=str(r.name),
                building_id=int(r.building_id),
                distance_m=None,
            )
            for r in rows
        ]
        return Page(total=total, items=items)
