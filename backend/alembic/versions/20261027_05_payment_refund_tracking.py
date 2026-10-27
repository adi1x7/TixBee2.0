"""track local cancellation refunds

Revision ID: 20261027_05
Revises: 20261026_04
Create Date: 2026-10-27
"""

from alembic import op
import sqlalchemy as sa


revision = "20261027_05"
down_revision = "20261026_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("payments")}
    if "refund_amount" not in columns:
        op.add_column("payments", sa.Column("refund_amount", sa.Integer(), nullable=True))
    if "refund_status" not in columns:
        op.add_column("payments", sa.Column("refund_status", sa.String(length=24), nullable=True))
    if "refunded_at" not in columns:
        op.add_column("payments", sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("payments")}
    for column in ("refunded_at", "refund_status", "refund_amount"):
        if column in columns:
            op.drop_column("payments", column)
