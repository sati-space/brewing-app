"""add preferred temperature unit for users

Revision ID: 20260227_11
Revises: 20260227_10
Create Date: 2026-02-27 20:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260227_11"
down_revision: Union[str, None] = "20260227_10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("preferred_temperature_unit", sa.String(length=1), nullable=False, server_default="C"),
    )


def downgrade() -> None:
    op.drop_column("users", "preferred_temperature_unit")
