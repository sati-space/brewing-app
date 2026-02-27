"""add water profiles for water chemistry recommendations

Revision ID: 20260227_09
Revises: 20260227_08
Create Date: 2026-02-27 17:20:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260227_09"
down_revision: Union[str, None] = "20260227_08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "water_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("calcium_ppm", sa.Float(), nullable=False),
        sa.Column("magnesium_ppm", sa.Float(), nullable=False),
        sa.Column("sodium_ppm", sa.Float(), nullable=False),
        sa.Column("chloride_ppm", sa.Float(), nullable=False),
        sa.Column("sulfate_ppm", sa.Float(), nullable=False),
        sa.Column("bicarbonate_ppm", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_user_id", "name", name="uq_water_profile_owner_name"),
    )
    op.create_index(op.f("ix_water_profiles_id"), "water_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_water_profiles_owner_user_id"), "water_profiles", ["owner_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_water_profiles_owner_user_id"), table_name="water_profiles")
    op.drop_index(op.f("ix_water_profiles_id"), table_name="water_profiles")
    op.drop_table("water_profiles")
