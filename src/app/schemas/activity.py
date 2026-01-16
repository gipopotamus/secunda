from __future__ import annotations

from pydantic import BaseModel


class ActivityOut(BaseModel):
    id: int
    name: str
    parent_id: int | None
    depth: int


class ActivityNode(ActivityOut):
    children: list[ActivityNode] = []


ActivityNode.model_rebuild()
