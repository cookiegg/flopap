"""rename_user_recommendation_pools_to_user_paper_rankings

Revision ID: 54c12d244a63
Revises: rename_infographics
Create Date: 2025-12-22 21:45:20.636433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54c12d244a63'
down_revision: Union[str, Sequence[str], None] = 'rename_infographics'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 重命名表
    op.rename_table('user_recommendation_pools', 'user_paper_rankings')
    
    # 重命名相关索引
    op.execute('ALTER INDEX idx_user_pool_date RENAME TO idx_user_ranking_date')
    op.execute('ALTER INDEX uq_user_pool_date_source RENAME TO uq_user_ranking_date_source')


def downgrade() -> None:
    """Downgrade schema."""
    # 回滚操作
    op.rename_table('user_paper_rankings', 'user_recommendation_pools')
    op.execute('ALTER INDEX idx_user_ranking_date RENAME TO idx_user_pool_date')
    op.execute('ALTER INDEX uq_user_ranking_date_source RENAME TO uq_user_pool_date_source')
