from __future__ import annotations

from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession


class Repo(ABC):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
