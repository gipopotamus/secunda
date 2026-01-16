from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Activity(Base):
    __tablename__ = "activities"

    __table_args__ = (
        CheckConstraint("depth >= 1 AND depth <= 3", name="depth_range_1_3"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"),
        nullable=True,
    )

    depth: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    parent: Mapped[Activity | None] = relationship(
        remote_side="Activity.id",
        back_populates="children",
    )

    children: Mapped[list[Activity]] = relationship(
        back_populates="parent",
    )

    organizations: Mapped[list[Organization]] = relationship(
        secondary="organization_activities",
        back_populates="activities",
    )
