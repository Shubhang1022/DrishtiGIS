"""Initial schema — all DrishtiGIS tables + spatial indexes

Revision ID: 001
Revises: 
Create Date: 2026-09-08

Tables created:
  users, datasets, parcels, properties, ai_features,
  discrepancies, processing_jobs, historical_snapshots

Notes:
  - All geometry columns use SRID 4326 (WGS84 geographic)
  - GIST spatial indexes on all geometry columns
  - PostGIS extension created if not exists
  - change_type on historical_snapshots is explicitly nullable:
    NULL = no multi-temporal imagery available for prototype dataset
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostGIS extension (no-op if already installed; safe on Supabase)
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # ------------------------------------------------------------------ users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("role", sa.Text(), nullable=False, server_default="user"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # --------------------------------------------------------------- datasets
    op.create_table(
        "datasets",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("dataset_type", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("crs", sa.Text(), nullable=True),
        sa.Column("bounds", sa.Text(), nullable=True),          # geometry(Polygon,4326) via PostGIS
        sa.Column("resolution_m", sa.Numeric(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="uploaded"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    # Alter bounds to proper geometry after table creation (PostGIS DDL)
    op.execute("ALTER TABLE datasets ALTER COLUMN bounds TYPE geometry(Polygon,4326) USING bounds::geometry")
    op.execute("CREATE INDEX IF NOT EXISTS idx_datasets_bounds ON datasets USING GIST (bounds)")

    # ---------------------------------------------------------------- parcels
    op.create_table(
        "parcels",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("property_id", sa.Text(), nullable=True),
        sa.Column("plot_number", sa.Text(), nullable=True),
        sa.Column("survey_number", sa.Text(), nullable=True),
        sa.Column("area_m2", sa.Numeric(), nullable=True),
        sa.Column("land_type", sa.Text(), nullable=True),
        sa.Column("geometry", sa.Text(), nullable=True),        # geometry(MultiPolygon,4326)
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("dataset_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("property_id"),
    )
    op.execute("ALTER TABLE parcels ALTER COLUMN geometry TYPE geometry(MultiPolygon,4326) USING geometry::geometry")
    op.execute("CREATE INDEX IF NOT EXISTS idx_parcels_geometry ON parcels USING GIST (geometry)")

    # ------------------------------------------------------------- properties
    op.create_table(
        "properties",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("parcel_id", sa.UUID(), nullable=True),
        sa.Column("property_id", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("land_type", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["parcel_id"], ["parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("property_id"),
    )

    # ------------------------------------------------------------ ai_features
    op.create_table(
        "ai_features",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dataset_id", sa.UUID(), nullable=True),
        sa.Column("feature_type", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(), nullable=True),
        sa.Column("area_m2", sa.Numeric(), nullable=True),
        sa.Column("geometry", sa.Text(), nullable=True),        # geometry(MultiPolygon,4326)
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("model_version", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_ai_features_confidence"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("ALTER TABLE ai_features ALTER COLUMN geometry TYPE geometry(MultiPolygon,4326) USING geometry::geometry")
    op.execute("CREATE INDEX IF NOT EXISTS idx_ai_features_geometry ON ai_features USING GIST (geometry)")

    # ---------------------------------------------------------- discrepancies
    op.create_table(
        "discrepancies",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("parcel_id", sa.UUID(), nullable=True),
        sa.Column("feature_id", sa.UUID(), nullable=True),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("official_value", sa.Numeric(), nullable=True),
        sa.Column("ai_value", sa.Numeric(), nullable=True),
        sa.Column("difference", sa.Numeric(), nullable=True),
        sa.Column("difference_pct", sa.Numeric(), nullable=True),
        sa.Column("severity", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True, server_default="pending_review"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["feature_id"], ["ai_features.id"]),
        sa.ForeignKeyConstraint(["parcel_id"], ["parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_discrepancies_parcel_id ON discrepancies (parcel_id)")

    # ------------------------------------------------------- processing_jobs
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dataset_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="queued"),
        sa.Column("progress", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("progress BETWEEN 0 AND 100", name="ck_processing_jobs_progress"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # -------------------------------------------------- historical_snapshots
    op.create_table(
        "historical_snapshots",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("property_id", sa.UUID(), nullable=True),
        sa.Column("dataset_id", sa.UUID(), nullable=True),
        sa.Column("captured_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("imagery_source", sa.Text(), nullable=False),
        sa.Column("geometry", sa.Text(), nullable=True),        # geometry(MultiPolygon,4326)
        sa.Column(
            "change_type",
            sa.Text(),
            nullable=True,
            # Explicitly nullable:
            # NULL = no historical change classification available because
            # no real multi-temporal imagery exists for the prototype dataset.
        ),
        sa.Column("confidence", sa.Numeric(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_historical_snapshots_confidence"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("ALTER TABLE historical_snapshots ALTER COLUMN geometry TYPE geometry(MultiPolygon,4326) USING geometry::geometry")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_snapshots_geometry ON historical_snapshots USING GIST (geometry)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_snapshots_property_id ON historical_snapshots (property_id)")


def downgrade() -> None:
    op.drop_table("historical_snapshots")
    op.drop_table("processing_jobs")
    op.drop_table("discrepancies")
    op.drop_table("ai_features")
    op.drop_table("properties")
    op.drop_table("parcels")
    op.drop_table("datasets")
    op.drop_table("users")
