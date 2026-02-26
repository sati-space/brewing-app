"""user-scope inventory and low-stock support

Revision ID: 20260225_03
Revises: 20260225_02
Create Date: 2026-02-26 09:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260225_03"
down_revision: Union[str, None] = "20260225_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_items_new",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("ingredient_type", sa.String(length=30), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("low_stock_threshold", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_user_id", "name", name="uq_inventory_items_owner_name"),
    )

    op.execute(
        """
        INSERT INTO inventory_items_new (name, ingredient_type, quantity, unit, low_stock_threshold, updated_at)
        SELECT name, ingredient_type, quantity, unit, low_stock_threshold, updated_at
        FROM inventory_items
        """
    )

    op.drop_index(op.f("ix_inventory_items_id"), table_name="inventory_items")
    op.drop_table("inventory_items")
    op.rename_table("inventory_items_new", "inventory_items")

    op.create_index(op.f("ix_inventory_items_id"), "inventory_items", ["id"], unique=False)
    op.create_index(op.f("ix_inventory_items_owner_user_id"), "inventory_items", ["owner_user_id"], unique=False)


def downgrade() -> None:
    op.create_table(
        "inventory_items_old",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("ingredient_type", sa.String(length=30), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("low_stock_threshold", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.execute(
        """
        INSERT INTO inventory_items_old (name, ingredient_type, quantity, unit, low_stock_threshold, updated_at)
        SELECT i.name, i.ingredient_type, i.quantity, i.unit, i.low_stock_threshold, i.updated_at
        FROM inventory_items i
        WHERE i.id IN (
            SELECT MIN(ii.id)
            FROM inventory_items ii
            GROUP BY ii.name
        )
        """
    )

    op.drop_index(op.f("ix_inventory_items_owner_user_id"), table_name="inventory_items")
    op.drop_index(op.f("ix_inventory_items_id"), table_name="inventory_items")
    op.drop_table("inventory_items")
    op.rename_table("inventory_items_old", "inventory_items")

    op.create_index(op.f("ix_inventory_items_id"), "inventory_items", ["id"], unique=False)
