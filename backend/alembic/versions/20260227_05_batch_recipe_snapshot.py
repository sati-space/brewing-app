"""add batch recipe snapshot columns

Revision ID: 20260227_05
Revises: 20260226_04
Create Date: 2026-02-27 14:15:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260227_05"
down_revision: Union[str, None] = "20260226_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("batches", sa.Column("recipe_snapshot_captured_at", sa.DateTime(), nullable=True))
    op.add_column("batches", sa.Column("recipe_name_snapshot", sa.String(length=140), nullable=True))
    op.add_column("batches", sa.Column("recipe_style_snapshot", sa.String(length=80), nullable=True))
    op.add_column("batches", sa.Column("recipe_target_og_snapshot", sa.Float(), nullable=True))
    op.add_column("batches", sa.Column("recipe_target_fg_snapshot", sa.Float(), nullable=True))
    op.add_column("batches", sa.Column("recipe_target_ibu_snapshot", sa.Float(), nullable=True))
    op.add_column("batches", sa.Column("recipe_target_srm_snapshot", sa.Float(), nullable=True))
    op.add_column("batches", sa.Column("recipe_efficiency_pct_snapshot", sa.Float(), nullable=True))
    op.add_column("batches", sa.Column("recipe_notes_snapshot", sa.Text(), nullable=True))
    op.add_column("batches", sa.Column("recipe_ingredients_snapshot_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("batches", "recipe_ingredients_snapshot_json")
    op.drop_column("batches", "recipe_notes_snapshot")
    op.drop_column("batches", "recipe_efficiency_pct_snapshot")
    op.drop_column("batches", "recipe_target_srm_snapshot")
    op.drop_column("batches", "recipe_target_ibu_snapshot")
    op.drop_column("batches", "recipe_target_fg_snapshot")
    op.drop_column("batches", "recipe_target_og_snapshot")
    op.drop_column("batches", "recipe_style_snapshot")
    op.drop_column("batches", "recipe_name_snapshot")
    op.drop_column("batches", "recipe_snapshot_captured_at")
