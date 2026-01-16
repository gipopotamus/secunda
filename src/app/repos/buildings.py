from __future__ import annotations

from geoalchemy2 import Geometry
from sqlalchemy import cast, func, select

from app.models.building import Building
from app.repos.base import Repo
from app.repos.dto import BuildingRow, Page


class BuildingsRepo(Repo):
    async def list(self, *, limit: int, offset: int) -> Page[BuildingRow]:
        total_stmt = select(func.count()).select_from(select(Building.id).subquery())
        total = int(await self.session.scalar(total_stmt) or 0)

        geom_as_geom = cast(Building.geom, Geometry(geometry_type="POINT", srid=4326))

        stmt = (
            select(
                Building.id.label("id"),
                Building.address.label("address"),
                func.ST_Y(geom_as_geom).label("lat"),
                func.ST_X(geom_as_geom).label("lon"),
            )
            .order_by(Building.id.asc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.session.execute(stmt)).all()
        items = [
            BuildingRow(
                id=int(r.id),
                address=str(r.address),
                lat=float(r.lat),
                lon=float(r.lon),
            )
            for r in rows
        ]
        return Page(total=total, items=items)
