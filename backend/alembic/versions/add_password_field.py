"""add password field

Revision ID: add_password_field
Revises: ac7f81a46a67
Create Date: 2025-12-07 02:23:00

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_password_field'
down_revision = 'ac7f81a46a67'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 password_hash 字段
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    
    # 修改 oauth_provider 和 oauth_id 为可空（支持本地账号）
    op.alter_column('users', 'oauth_provider',
                    existing_type=sa.String(32),
                    nullable=True,
                    new_column_name='provider')
    op.alter_column('users', 'oauth_id',
                    existing_type=sa.String(255),
                    nullable=True)


def downgrade() -> None:
    op.drop_column('users', 'password_hash')
    op.alter_column('users', 'provider',
                    existing_type=sa.String(32),
                    nullable=False,
                    new_column_name='oauth_provider')
    op.alter_column('users', 'oauth_id',
                    existing_type=sa.String(255),
                    nullable=False)
