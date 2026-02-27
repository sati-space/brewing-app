"""add equipment profiles for external imports

Revision ID: 20260227_07
Revises: 20260227_06
Create Date: 2026-02-27 16:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260227_07"
down_revision: Union[str, None] = "20260227_06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "equipment_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("source_provider", sa.String(length=60), nullable=False),
        sa.Column("source_external_id", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("batch_volume_liters", sa.Float(), nullable=False),
        sa.Column("mash_tun_volume_liters", sa.Float(), nullable=True),
        sa.Column("boil_kettle_volume_liters", sa.Float(), nullable=True),
        sa.Column("brewhouse_efficiency_pct", sa.Float(), nullable=False),
        sa.Column("boil_off_rate_l_per_hour", sa.Float(), nullable=True),
        sa.Column("trub_loss_liters", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_user_id", "source_provider", "source_external_id", name="uq_equipment_profile_source"),
    )
    op.create_index(op.f("ix_equipment_profiles_id"), "equipment_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_equipment_profiles_owner_user_id"), "equipment_profiles", ["owner_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_equipment_profiles_owner_user_id"), table_name="equipment_profiles")
    op.drop_index(op.f("ix_equipment_profiles_id"), table_name="equipment_profiles")
    op.drop_table("equipment_profiles")
