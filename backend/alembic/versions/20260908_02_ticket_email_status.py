"""record ticket email delivery state

Revision ID: 20260908_02
Revises: 20260908_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260908_02"
down_revision = "20260908_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("email_delivery_status", sa.String(length=24), nullable=False, server_default="PENDING"))


def downgrade() -> None:
    op.drop_column("tickets", "email_delivery_status")
