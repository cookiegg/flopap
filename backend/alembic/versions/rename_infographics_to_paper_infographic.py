"""rename infographics to paper_infographic and remove redundant field

Revision ID: rename_infographics
Revises: 5ee90d682b5b
Create Date: 2025-12-19 01:09:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rename_infographics'
down_revision = '5ee90d682b5b'
branch_labels = None
depends_on = None


def upgrade():
    # 重命名表
    op.rename_table('infographics', 'paper_infographics')
    
    # 移除paper_translations表中的infographic_html字段
    op.drop_column('paper_translations', 'infographic_html')


def downgrade():
    # 恢复paper_translations表中的infographic_html字段
    op.add_column('paper_translations', sa.Column('infographic_html', sa.TEXT(), nullable=True))
    
    # 恢复表名
    op.rename_table('paper_infographics', 'infographics')
