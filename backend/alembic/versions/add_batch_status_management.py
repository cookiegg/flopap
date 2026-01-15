"""Add batch status management

Revision ID: batch_status_001
Revises: 149a08bce4a4
Create Date: 2025-12-14 21:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'batch_status_001'
down_revision = '149a08bce4a4'
branch_labels = None
depends_on = None


def upgrade():
    # Create batch status enum
    batch_status_enum = postgresql.ENUM(
        'pending', 'processing', 'completed', 'failed', 'retrying',
        name='batchstatus'
    )
    batch_status_enum.create(op.get_bind())
    
    # Create batch_executions table
    op.create_table('batch_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', batch_status_enum, nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_papers', sa.Integer(), nullable=True),
        sa.Column('valid_papers', sa.Integer(), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('quality_report', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on batch_id for faster lookups
    op.create_index('ix_batch_executions_batch_id', 'batch_executions', ['batch_id'])
    op.create_index('ix_batch_executions_status', 'batch_executions', ['status'])
    op.create_index('ix_batch_executions_created_at', 'batch_executions', ['created_at'])


def downgrade():
    # Drop table and indexes
    op.drop_index('ix_batch_executions_created_at', table_name='batch_executions')
    op.drop_index('ix_batch_executions_status', table_name='batch_executions')
    op.drop_index('ix_batch_executions_batch_id', table_name='batch_executions')
    op.drop_table('batch_executions')
    
    # Drop enum
    batch_status_enum = postgresql.ENUM(name='batchstatus')
    batch_status_enum.drop(op.get_bind())
