"""add_data_source_pool_settings

Revision ID: add_pool_settings_001
Revises: 
Create Date: 2026-01-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_pool_settings_001'
down_revision = None  # Update this to latest migration ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'data_source_pool_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('source_key', sa.String(100), nullable=False, index=True),
        sa.Column('pool_ratio', sa.Float(), nullable=False, server_default='0.2'),
        sa.Column('max_pool_size', sa.Integer(), nullable=False, server_default='2000'),
        sa.Column('show_mode', sa.String(20), nullable=False, server_default='pool'),
        sa.Column('filter_no_content', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'source_key', name='uq_user_source_pool_settings'),
        sa.CheckConstraint('pool_ratio >= 0.0 AND pool_ratio <= 1.0', name='check_pool_ratio_range'),
        sa.CheckConstraint("show_mode IN ('pool', 'all')", name='check_show_mode'),
    )


def downgrade() -> None:
    op.drop_table('data_source_pool_settings')
