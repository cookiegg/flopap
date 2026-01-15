"""add user recommendation pool

Revision ID: add_user_recommendation_pool
Revises: 
Create Date: 2025-12-13 00:42:30.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_user_recommendation_pool'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建用户推荐池表
    op.create_table('user_recommendation_pools',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('pool_date', sa.Date(), nullable=False),
        sa.Column('paper_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
        sa.Column('scores', postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'pool_date', name='unique_user_pool_date')
    )
    
    # 创建索引
    op.create_index('ix_user_recommendation_pools_user_id', 'user_recommendation_pools', ['user_id'])
    op.create_index('ix_user_recommendation_pools_pool_date', 'user_recommendation_pools', ['pool_date'])


def downgrade():
    op.drop_table('user_recommendation_pools')
