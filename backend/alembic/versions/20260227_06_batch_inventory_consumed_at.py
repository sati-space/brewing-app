"""add batch inventory consumption timestamp

Revision ID: 20260227_06
Revises: 20260227_05
Create Date: 2026-02-27 15:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260227_06"
down_revision: Union[str, None] = "20260227_05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("batches", sa.Column("inventory_consumed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("batches", "inventory_consumed_at")
