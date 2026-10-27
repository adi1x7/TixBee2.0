"""scope staff users to one attraction

Revision ID: 20261026_03
Revises: 20260908_02
Create Date: 2026-10-26
"""

from alembic import op
import sqlalchemy as sa


revision = "20261026_03"
down_revision = "20260908_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Revision 01 creates current SQLAlchemy metadata on a fresh database, so
    # each operation must also be safe when the column already exists.
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "assigned_attraction_id" not in columns:
        op.add_column("users", sa.Column("assigned_attraction_id", sa.String(length=36), nullable=True))
        inspector = sa.inspect(op.get_bind())
    foreign_keys = {foreign_key.get("name") for foreign_key in inspector.get_foreign_keys("users")}
    if "fk_users_assigned_attraction_id_attractions" not in foreign_keys:
        op.create_foreign_key(
            "fk_users_assigned_attraction_id_attractions",
            "users",
            "attractions",
            ["assigned_attraction_id"],
            ["id"],
        )
    indexes = {index["name"] for index in inspector.get_indexes("users")}
    if "ix_users_assigned_attraction_id" not in indexes:
        op.create_index("ix_users_assigned_attraction_id", "users", ["assigned_attraction_id"])


def downgrade() -> None:
    op.drop_index("ix_users_assigned_attraction_id", table_name="users")
    op.drop_constraint("fk_users_assigned_attraction_id_attractions", "users", type_="foreignkey")
    op.drop_column("users", "assigned_attraction_id")
