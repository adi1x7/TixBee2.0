"""initial TixBee v1 schema

Revision ID: 20260908_01
Revises:
Create Date: 2026-09-08
"""

from alembic import op

from app.core.database import Base
import app.models  # noqa: F401 - registers all mapped tables

revision = "20260908_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
