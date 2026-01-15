"""Framework V2 core tables

Revision ID: framework_v2_core
Revises: ac7f81a46a67
Create Date: 2025-12-12 21:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'framework_v2_core'
down_revision = 'ac7f81a46a67'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 用户API密钥管理表
    op.create_table('user_api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('service_type', sa.String(length=50), nullable=False),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('key_salt', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'service_type')
    )
    op.create_index('idx_user_api_keys_user_id', 'user_api_keys', ['user_id'])
    op.create_index('idx_user_api_keys_service_type', 'user_api_keys', ['service_type'])

    # 用户推荐配置表
    op.create_table('user_recommendation_settings',
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('arxiv_ratio', sa.Integer(), nullable=True, default=10),
        sa.Column('conference_ratio', sa.Integer(), nullable=True, default=20),
        sa.Column('max_pool_size', sa.Integer(), nullable=True, default=50),
        sa.Column('enable_auto_generation', sa.Boolean(), nullable=True, default=False),
        sa.Column('preferred_models', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default=sa.text("'[]'")),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('user_id'),
        sa.CheckConstraint('arxiv_ratio BETWEEN 1 AND 50', name='check_arxiv_ratio'),
        sa.CheckConstraint('conference_ratio BETWEEN 1 AND 50', name='check_conference_ratio'),
        sa.CheckConstraint('max_pool_size BETWEEN 10 AND 200', name='check_max_pool_size')
    )

    # 用户生成内容表
    op.create_table('user_generated_content',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('content_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('model_used', sa.String(length=100), nullable=False),
        sa.Column('generation_cost', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('is_shared', sa.Boolean(), nullable=True, default=True),
        sa.Column('quality_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE')
    )
    op.create_index('idx_user_generated_content_paper_type', 'user_generated_content', ['paper_id', 'content_type'])
    op.create_index('idx_user_generated_content_user_created', 'user_generated_content', ['user_id', 'created_at'])

    # 管理员推送内容表
    op.create_table('admin_pushed_content',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('content_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True, default=1),
        sa.Column('target_users', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE')
    )
    op.create_index('idx_admin_pushed_content_paper_id', 'admin_pushed_content', ['paper_id'])
    op.create_index('idx_admin_pushed_content_priority', 'admin_pushed_content', ['priority'])

    # 内容生成任务队列表
    op.create_table('content_generation_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('paper_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('progress', sa.Integer(), nullable=True, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('estimated_cost', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('actual_cost', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE')
    )
    op.create_index('idx_content_generation_tasks_status', 'content_generation_tasks', ['status'])
    op.create_index('idx_content_generation_tasks_user_id', 'content_generation_tasks', ['user_id'])

    # 扩展user_profiles表
    op.add_column('user_profiles', sa.Column('api_quota_used', sa.Integer(), nullable=True, default=0))
    op.add_column('user_profiles', sa.Column('api_quota_limit', sa.Integer(), nullable=True, default=1000))
    op.add_column('user_profiles', sa.Column('subscription_tier', sa.String(length=20), nullable=True, default='free'))

    # 添加性能索引
    op.create_index('idx_paper_translations_model_created', 'paper_translations', ['model_name', 'created_at'])
    op.create_index('idx_papers_categories_gin', 'papers', ['categories'], postgresql_using='gin')
    op.create_index('idx_papers_submitted_date', 'papers', ['submitted_date'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_papers_submitted_date', table_name='papers')
    op.drop_index('idx_papers_categories_gin', table_name='papers')
    op.drop_index('idx_paper_translations_model_created', table_name='paper_translations')
    
    # 删除user_profiles扩展列
    op.drop_column('user_profiles', 'subscription_tier')
    op.drop_column('user_profiles', 'api_quota_limit')
    op.drop_column('user_profiles', 'api_quota_used')
    
    # 删除表
    op.drop_table('content_generation_tasks')
    op.drop_table('admin_pushed_content')
    op.drop_table('user_generated_content')
    op.drop_table('user_recommendation_settings')
    op.drop_table('user_api_keys')
