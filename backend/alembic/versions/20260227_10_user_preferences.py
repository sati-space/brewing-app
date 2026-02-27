"""add user language and unit-system preferences

Revision ID: 20260227_10
Revises: 20260227_09
Create Date: 2026-02-27 19:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260227_10"
down_revision: Union[str, None] = "20260227_09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("preferred_unit_system", sa.String(length=10), nullable=False, server_default="metric"),
    )
    op.add_column(
        "users",
        sa.Column("preferred_language", sa.String(length=5), nullable=False, server_default="en"),
    )


def downgrade() -> None:
    op.drop_column("users", "preferred_language")
    op.drop_column("users", "preferred_unit_system")
