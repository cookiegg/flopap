"""add_paper_translation

Revision ID: be7a3f79d8dc
Revises: 9a3a3dc34976
Create Date: 2025-01-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'be7a3f79d8dc'
down_revision: Union[str, Sequence[str], None] = '9a3a3dc34976'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 paper_translations 表"""
    op.create_table(
        'paper_translations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title_zh', sa.Text(), nullable=True),
        sa.Column('summary_zh', sa.Text(), nullable=True),
        sa.Column('ai_interpretation', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=256), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('paper_id'),
        comment='存储推荐池中论文的中文翻译和AI解读'
    )
    op.create_index(op.f('ix_paper_translations_paper_id'), 'paper_translations', ['paper_id'], unique=False)


def downgrade() -> None:
    """删除 paper_translations 表"""
    op.drop_index(op.f('ix_paper_translations_paper_id'), table_name='paper_translations')
    op.drop_table('paper_translations')

