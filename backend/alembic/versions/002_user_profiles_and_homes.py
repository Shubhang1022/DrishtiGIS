"""Supabase user profiles and isolated HOME locations schema

Revision ID: 002
Revises: 001
Create Date: 2026-10-06

Tables created:
  drishtigis_user_profiles: Stores real-user metadata mapped to Supabase Auth UUID
  user_home_locations: Stores private, isolated HOME coordinates per authenticated user
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------ drishtigis_user_profiles
    op.create_table(
        "drishtigis_user_profiles",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("supabase_user_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("organization", sa.Text(), nullable=True),
        sa.Column("role", sa.Text(), nullable=False, server_default="PUBLIC"),
        sa.Column("country", sa.Text(), nullable=False, server_default="India"),
        sa.Column("state", sa.Text(), nullable=True, server_default="Madhya Pradesh"),
        sa.Column("city", sa.Text(), nullable=True, server_default="Bhopal"),
        sa.Column("region_id", sa.Text(), nullable=True, server_default="bhopal_mp"),
        sa.Column("allowed_datasets", sa.JSON(), nullable=False, server_default=sa.text("'[\"*\"]'::json")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supabase_user_id"),
    )
    op.create_index("ix_drishtigis_user_profiles_sb_uid", "drishtigis_user_profiles", ["supabase_user_id"])
    op.create_index("ix_drishtigis_user_profiles_email", "drishtigis_user_profiles", ["email"])

    # ------------------------------------------------ user_home_locations
    op.create_table(
        "user_home_locations",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("address_label", sa.Text(), nullable=False, server_default="HOME"),
        sa.Column("accuracy_m", sa.Float(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_home_locations_user_id", "user_home_locations", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_home_locations")
    op.drop_table("drishtigis_user_profiles")
