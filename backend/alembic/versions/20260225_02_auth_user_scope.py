"""add users and ownership scoping

Revision ID: 20260225_02
Revises: 20260225_01
Create Date: 2026-02-25 15:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260225_02"
down_revision: Union[str, None] = "20260225_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=40), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    with op.batch_alter_table("recipes") as batch_op:
        batch_op.add_column(sa.Column("owner_user_id", sa.Integer(), nullable=True))
        batch_op.create_index(op.f("ix_recipes_owner_user_id"), ["owner_user_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_recipes_owner_user_id_users",
            "users",
            ["owner_user_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("batches") as batch_op:
        batch_op.add_column(sa.Column("owner_user_id", sa.Integer(), nullable=True))
        batch_op.create_index(op.f("ix_batches_owner_user_id"), ["owner_user_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_batches_owner_user_id_users",
            "users",
            ["owner_user_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("batches") as batch_op:
        batch_op.drop_constraint("fk_batches_owner_user_id_users", type_="foreignkey")
        batch_op.drop_index(op.f("ix_batches_owner_user_id"))
        batch_op.drop_column("owner_user_id")

    with op.batch_alter_table("recipes") as batch_op:
        batch_op.drop_constraint("fk_recipes_owner_user_id_users", type_="foreignkey")
        batch_op.drop_index(op.f("ix_recipes_owner_user_id"))
        batch_op.drop_column("owner_user_id")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
