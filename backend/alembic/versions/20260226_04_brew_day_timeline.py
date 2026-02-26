"""add brew day timeline steps

Revision ID: 20260226_04
Revises: 20260225_03
Create Date: 2026-02-26 10:05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260226_04"
down_revision: Union[str, None] = "20260225_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brew_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("target_temp_c", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_brew_steps_id"), "brew_steps", ["id"], unique=False)
    op.create_index(op.f("ix_brew_steps_batch_id"), "brew_steps", ["batch_id"], unique=False)
    op.create_index(op.f("ix_brew_steps_owner_user_id"), "brew_steps", ["owner_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_brew_steps_owner_user_id"), table_name="brew_steps")
    op.drop_index(op.f("ix_brew_steps_batch_id"), table_name="brew_steps")
    op.drop_index(op.f("ix_brew_steps_id"), table_name="brew_steps")
    op.drop_table("brew_steps")
