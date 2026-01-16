from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

organization_activities = Table(
    "organization_activities",
    Base.metadata,
    sa.Column(
        "organization_id",
        sa.Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "activity_id",
        sa.Integer,
        ForeignKey("activities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)

    building_id: Mapped[int] = mapped_column(
        ForeignKey("buildings.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    building: Mapped[Building] = relationship(back_populates="organizations")

    phones: Mapped[list[OrganizationPhone]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    activities: Mapped[list[Activity]] = relationship(
        secondary=organization_activities,
        back_populates="organizations",
    )


class OrganizationPhone(Base):
    __tablename__ = "organization_phones"
    __table_args__ = (
        UniqueConstraint("organization_id", "phone", name="org_phone_unique"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    phone: Mapped[str] = mapped_column(String(32), nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="phones")
