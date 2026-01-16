from __future__ import annotations

from geoalchemy2 import Geography
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)

    geom: Mapped[object] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    organizations: Mapped[list[Organization]] = relationship(
        back_populates="building",
        cascade="all, delete-orphan",
    )
