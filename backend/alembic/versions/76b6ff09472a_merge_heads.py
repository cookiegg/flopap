"""merge_heads

Revision ID: 76b6ff09472a
Revises: batch_status_001, add_user_recommendation_pool
Create Date: 2025-12-15 15:12:58.339531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76b6ff09472a'
down_revision: Union[str, Sequence[str], None] = ('batch_status_001', 'add_user_recommendation_pool')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
