"""add_user_profile

Revision ID: 9a3a3dc34976
Revises: 0001_initial_schema
Create Date: 2025-11-04 02:54:27.639271

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9a3a3dc34976'
down_revision: Union[str, Sequence[str], None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 user_profiles 表"""
    op.create_table(
        'user_profiles',
    sa.Column('user_id', sa.String(length=64), nullable=False),
    sa.Column('interested_categories', postgresql.ARRAY(sa.String(length=128)), nullable=False),
    sa.Column('research_keywords', postgresql.ARRAY(sa.String(length=256)), nullable=False),
    sa.Column('preference_description', sa.Text(), nullable=True),
    sa.Column('onboarding_completed', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('user_id'),
    comment='用户偏好和兴趣资料，用于个性化推荐'
    )


def downgrade() -> None:
    """删除 user_profiles 表"""
    op.drop_table('user_profiles')
