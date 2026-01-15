"""add infographic_html field

Revision ID: add_infographic_html
Revises: be7a3f79d8dc
Create Date: 2025-12-06 21:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_infographic_html'
down_revision = 'be7a3f79d8dc'
branch_labels = None
depends_on = None


def upgrade():
    # 在 paper_translations 表添加 infographic_html 字段
    op.add_column('paper_translations', 
        sa.Column('infographic_html', sa.Text(), nullable=True)
    )


def downgrade():
    op.drop_column('paper_translations', 'infographic_html')
