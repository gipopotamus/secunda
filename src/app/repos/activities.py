from __future__ import annotations

from sqlalchemy import func, select

from app.models.activity import Activity
from app.repos.base import Repo
from app.repos.dto import ActivityRow, Page


class ActivitiesRepo(Repo):
    async def list(self, *, limit: int, offset: int, max_depth: int = 3) -> Page[ActivityRow]:
        total_stmt = select(func.count()).select_from(
            select(Activity.id).where(Activity.depth <= max_depth).subquery()
        )
        total = int(await self.session.scalar(total_stmt) or 0)

        stmt = (
            select(Activity)
            .where(Activity.depth <= max_depth)
            .order_by(Activity.depth.asc(), Activity.id.asc())
            .limit(limit)
            .offset(offset)
        )
        items_orm = (await self.session.scalars(stmt)).all()
        items = [
            ActivityRow(id=a.id, name=a.name, parent_id=a.parent_id, depth=int(a.depth))
            for a in items_orm
        ]
        return Page(total=total, items=items)

    async def list_all(self, *, max_depth: int = 3) -> list[ActivityRow]:
        stmt = (
            select(Activity)
            .where(Activity.depth <= max_depth)
            .order_by(Activity.depth.asc(), Activity.id.asc())
        )
        items_orm = (await self.session.scalars(stmt)).all()
        return [
            ActivityRow(id=a.id, name=a.name, parent_id=a.parent_id, depth=int(a.depth))
            for a in items_orm
        ]

    async def subtree_ids(self, *, root_id: int, max_depth: int = 3) -> list[int]:
        """
        Returns ids of root activity and descendants (recursive CTE).
        """
        base = select(Activity.id, Activity.parent_id, Activity.depth).where(Activity.id == root_id)
        tree = base.cte(name="activity_tree", recursive=True)

        step = (
            select(Activity.id, Activity.parent_id, Activity.depth)
            .join(tree, Activity.parent_id == tree.c.id)
            .where(Activity.depth <= max_depth)
        )
        tree = tree.union_all(step)

        stmt = select(tree.c.id)
        return list((await self.session.scalars(stmt)).all())
