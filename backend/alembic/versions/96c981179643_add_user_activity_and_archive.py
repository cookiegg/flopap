"""add_user_activity_and_archive

Revision ID: 96c981179643
Revises: be7a3f79d8dc
Create Date: 2025-11-28 20:24:18.461778

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96c981179643'
down_revision: Union[str, Sequence[str], None] = 'be7a3f79d8dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 创建用户活动表
    op.create_table(
        'user_activity',
        sa.Column('user_id', sa.String(255), primary_key=True),
        sa.Column('last_open_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_feed_date', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # 为推荐池添加归档时间字段
    op.add_column('daily_recommendation_pool', 
                  sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))
    
    # 添加索引
    op.create_index('ix_user_activity_last_open_time', 'user_activity', ['last_open_time'])
    op.create_index('ix_daily_recommendation_pool_archived', 'daily_recommendation_pool', ['archived_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_daily_recommendation_pool_archived', 'daily_recommendation_pool')
    op.drop_index('ix_user_activity_last_open_time', 'user_activity')
    op.drop_column('daily_recommendation_pool', 'archived_at')
    op.drop_table('user_activity')
