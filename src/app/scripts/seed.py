from __future__ import annotations

import argparse
from dataclasses import dataclass

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.asyncio_win import install_windows_selector_event_loop
from app.db.session import AsyncSessionMaker
from app.models.activity import Activity
from app.models.building import Building
from app.models.organization import Organization, OrganizationPhone, organization_activities

install_windows_selector_event_loop()


@dataclass(frozen=True, slots=True)
class SeedOrg:
    name: str
    phones: list[str]
    activity_ids: list[int]
    building_id: int


def _wkt_point(lon: float, lat: float) -> str:
    return f"POINT({lon} {lat})"


async def _truncate(session: AsyncSession) -> None:
    # порядок важен из-за FK
    await session.execute(delete(OrganizationPhone))
    await session.execute(delete(organization_activities))
    await session.execute(delete(Organization))
    await session.execute(delete(Building))
    await session.execute(delete(Activity))


async def _seed_activities(session: AsyncSession) -> dict[str, int]:
    """
    Создаем дерево глубиной до 3:
    - Food
      - Cafe
      - Restaurant
    - Services
      - Barber
      - Repair
        - Phone repair
    - Health
      - Pharmacy
    """
    to_create = [
        {"name": "Food", "parent_id": None, "depth": 1},
        {"name": "Services", "parent_id": None, "depth": 1},
        {"name": "Health", "parent_id": None, "depth": 1},
    ]
    rows = (await session.execute(insert(Activity).returning(Activity.id, Activity.name), to_create)).all()
    root_ids = {r.name: int(r.id) for r in rows}

    to_create2 = [
        {"name": "Cafe", "parent_id": root_ids["Food"], "depth": 2},
        {"name": "Restaurant", "parent_id": root_ids["Food"], "depth": 2},
        {"name": "Barber", "parent_id": root_ids["Services"], "depth": 2},
        {"name": "Repair", "parent_id": root_ids["Services"], "depth": 2},
        {"name": "Pharmacy", "parent_id": root_ids["Health"], "depth": 2},
    ]
    rows2 = (await session.execute(insert(Activity).returning(Activity.id, Activity.name), to_create2)).all()
    lvl2 = {r.name: int(r.id) for r in rows2}

    to_create3 = [
        {"name": "Phone repair", "parent_id": lvl2["Repair"], "depth": 3},
    ]
    rows3 = (await session.execute(insert(Activity).returning(Activity.id, Activity.name), to_create3)).all()
    lvl3 = {r.name: int(r.id) for r in rows3}

    return {**root_ids, **lvl2, **lvl3}


async def _seed_buildings(session: AsyncSession) -> dict[str, int]:
    """
    3 здания с геоточками (примерно София, но не важно).
    """
    to_create = [
        {"address": "Sofia Center, ul. Graf Ignatiev 10", "geom": _wkt_point(23.3219, 42.6977)},
        {"address": "Sofia, Blvd. Vitosha 80", "geom": _wkt_point(23.3196, 42.6886)},
        {"address": "Sofia, Studentski grad", "geom": _wkt_point(23.3476, 42.6504)},
    ]
    rows = (await session.execute(insert(Building).returning(Building.id, Building.address), to_create)).all()
    return {r.address: int(r.id) for r in rows}


async def _seed_organizations(session: AsyncSession, *, act: dict[str, int], bld: dict[str, int]) -> None:
    b1 = bld["Sofia Center, ul. Graf Ignatiev 10"]
    b2 = bld["Sofia, Blvd. Vitosha 80"]
    b3 = bld["Sofia, Studentski grad"]

    orgs: list[SeedOrg] = [
        SeedOrg(name="Cafe Luna", phones=["+359888111222"], activity_ids=[act["Cafe"]], building_id=b1),
        SeedOrg(name="Vitosha Barber", phones=["+359888333444"], activity_ids=[act["Barber"]], building_id=b2),
        SeedOrg(name="FixIt Repair", phones=["+359888555666"], activity_ids=[act["Repair"], act["Phone repair"]], building_id=b3),
        SeedOrg(name="Healthy Pharmacy", phones=["+359888777888"], activity_ids=[act["Pharmacy"]], building_id=b2),
        SeedOrg(name="Restaurant Orion", phones=["+359888999000", "+359887000999"], activity_ids=[act["Restaurant"]], building_id=b1),
    ]

    # вставляем организации
    org_rows = (await session.execute(
        insert(Organization).returning(Organization.id, Organization.name),
        [{"name": o.name, "building_id": o.building_id} for o in orgs],
    )).all()
    org_id_by_name = {r.name: int(r.id) for r in org_rows}

    # телефоны
    phone_rows = []
    for o in orgs:
        oid = org_id_by_name[o.name]
        for p in o.phones:
            phone_rows.append({"organization_id": oid, "phone": p})
    if phone_rows:
        await session.execute(insert(OrganizationPhone), phone_rows)

    # m2m activities
    m2m_rows = []
    for o in orgs:
        oid = org_id_by_name[o.name]
        for aid in o.activity_ids:
            m2m_rows.append({"organization_id": oid, "activity_id": aid})
    if m2m_rows:
        await session.execute(insert(organization_activities), m2m_rows)


async def run(*, truncate: bool) -> None:
    async with AsyncSessionMaker() as session:
        async with session.begin():
            if truncate:
                await _truncate(session)

            act = await _seed_activities(session)
            bld = await _seed_buildings(session)
            await _seed_organizations(session, act=act, bld=bld)

        # после commit покажем подсказки
        a_any = await session.scalar(select(Activity.id).order_by(Activity.id.asc()).limit(1))
        print("Seed OK.")
        print("Try:")
        print("  GET /api/v1/activities/tree")
        if a_any is not None:
            print(f"  GET /api/v1/organizations/by-activity/{int(a_any)}?include_descendants=true")
        print("  GET /api/v1/organizations?name=cafe")
        print("  GET /api/v1/organizations/geo?lat=42.6977&lon=23.3219&radius_m=2000")
        print("  GET /api/v1/organizations/geo?min_lat=42.68&min_lon=23.30&max_lat=42.71&max_lon=23.33")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--truncate", action="store_true", help="Delete all rows from our tables first")
    args = parser.parse_args()

    import asyncio

    asyncio.run(run(truncate=bool(args.truncate)))


if __name__ == "__main__":
    main()
