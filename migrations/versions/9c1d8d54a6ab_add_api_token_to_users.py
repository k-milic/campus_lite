"""add api token to users

Revision ID: 9c1d8d54a6ab
Revises: 4dd6ae7e1264
Create Date: 2026-03-14 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9c1d8d54a6ab"
down_revision = "4dd6ae7e1264"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("api_token", sa.String(length=64), nullable=True)
    )
    op.create_index("ix_users_api_token", "users", ["api_token"], unique=True)


def downgrade():
    op.drop_index("ix_users_api_token", table_name="users")
    op.drop_column("users", "api_token")
