"""init schema

Revision ID: bfff833ba1f6
Revises: 
Create Date: 2026-01-16 17:41:57.597456

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'bfff833ba1f6'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Extensions (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # --- activities ---
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("depth", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("depth >= 1 AND depth <= 3", name="ck_activities_depth_1_3"),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["activities.id"],
            name="fk_activities_parent_id_activities",
            ondelete="SET NULL",
        ),
    )

    # --- buildings ---
    # geometry type is geography(Point, 4326), distances in meters
    op.create_table(
        "buildings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("geom", sa.Text(), nullable=False),
    )
    # Convert geom column from TEXT to geography(Point,4326)
    # We do it explicitly to avoid depending on geoalchemy2 autogen.
    op.execute(
        """
        ALTER TABLE buildings
        ALTER COLUMN geom
        TYPE geography(POINT, 4326)
        USING ST_GeogFromText(geom)
        """
    )

    # GIST index for geo queries
    op.execute("CREATE INDEX IF NOT EXISTS ix_buildings_geom_gist ON buildings USING gist (geom)")

    # --- organizations ---
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["building_id"],
            ["buildings.id"],
            name="fk_organizations_building_id_buildings",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_organizations_building_id", "organizations", ["building_id"], unique=False)

    # trigram gin for name search
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_organizations_name_trgm "
        "ON organizations USING gin (name gin_trgm_ops)"
    )

    # --- organization_activities (m2m) ---
    op.create_table(
        "organization_activities",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_org_acts_org_id_orgs",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["activities.id"],
            name="fk_org_acts_act_id_acts",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("organization_id", "activity_id", name="pk_organization_activities"),
    )
    op.create_index(
        "ix_org_acts_activity_id",
        "organization_activities",
        ["activity_id"],
        unique=False,
    )

    # --- organization_phones ---
    op.create_table(
        "organization_phones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_org_phones_org_id_orgs",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("organization_id", "phone", name="uq_org_phone"),
    )
    op.create_index(
        "ix_org_phones_organization_id",
        "organization_phones",
        ["organization_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse order
    op.drop_index("ix_org_phones_organization_id", table_name="organization_phones")
    op.drop_table("organization_phones")

    op.drop_index("ix_org_acts_activity_id", table_name="organization_activities")
    op.drop_table("organization_activities")

    op.execute("DROP INDEX IF EXISTS ix_organizations_name_trgm")
    op.drop_index("ix_organizations_building_id", table_name="organizations")
    op.drop_table("organizations")

    op.execute("DROP INDEX IF EXISTS ix_buildings_geom_gist")
    op.drop_table("buildings")

    op.drop_table("activities")

    # Extensions (optional to drop; safe)
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS postgis")