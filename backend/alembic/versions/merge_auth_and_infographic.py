"""merge auth and infographic

Revision ID: merge_auth_infographic
Revises: add_password_field, add_infographic_html
Create Date: 2025-12-07 02:40:00

"""
from alembic import op
import sqlalchemy as sa

revision = 'merge_auth_infographic'
down_revision = ('add_password_field', 'add_infographic_html')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
