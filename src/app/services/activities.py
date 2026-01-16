from __future__ import annotations

from dataclasses import dataclass

from app.repos.activities import ActivitiesRepo
from app.repos.dto import ActivityRow, Page

@dataclass(slots=True)
class ActivityNodeDTO:
    id: int
    name: str
    parent_id: int | None
    depth: int
    children: list["ActivityNodeDTO"]

class ActivitiesService:
    def __init__(self, repo: ActivitiesRepo) -> None:
        self.repo = repo

    async def list(self, *, limit: int, offset: int, max_depth: int = 3) -> Page[ActivityRow]:
        return await self.repo.list(limit=limit, offset=offset, max_depth=max_depth)

    async def tree(self, *, max_depth: int = 3) -> list[ActivityNodeDTO]:
        items = await self.repo.list_all(max_depth=max_depth)

        nodes: dict[int, ActivityNodeDTO] = {
            a.id: ActivityNodeDTO(id=a.id, name=a.name, parent_id=a.parent_id, depth=a.depth, children=[])
            for a in items
        }

        roots: list[ActivityNodeDTO] = []
        for n in nodes.values():
            if n.parent_id is None or n.parent_id not in nodes:
                roots.append(n)
            else:
                nodes[n.parent_id].children.append(n)

        def sort_tree(lst: list[ActivityNodeDTO]) -> None:
            lst.sort(key=lambda x: x.id)
            for x in lst:
                sort_tree(x.children)

        sort_tree(roots)
        return roots

    async def subtree_ids(self, *, root_id: int, max_depth: int = 3) -> list[int]:
        return await self.repo.subtree_ids(root_id=root_id, max_depth=max_depth)
