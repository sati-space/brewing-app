"""add ingredient profiles for ingredient APIs

Revision ID: 20260227_08
Revises: 20260227_07
Create Date: 2026-02-27 16:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260227_08"
down_revision: Union[str, None] = "20260227_07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingredient_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("source_provider", sa.String(length=60), nullable=True),
        sa.Column("source_external_id", sa.String(length=120), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("ingredient_type", sa.String(length=30), nullable=False),
        sa.Column("default_unit", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_user_id", "name", "ingredient_type", name="uq_ingredient_profile_name_type"),
        sa.UniqueConstraint("owner_user_id", "source_provider", "source_external_id", name="uq_ingredient_profile_source"),
    )
    op.create_index(op.f("ix_ingredient_profiles_id"), "ingredient_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_ingredient_profiles_owner_user_id"), "ingredient_profiles", ["owner_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ingredient_profiles_owner_user_id"), table_name="ingredient_profiles")
    op.drop_index(op.f("ix_ingredient_profiles_id"), table_name="ingredient_profiles")
    op.drop_table("ingredient_profiles")
