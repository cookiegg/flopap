"""merge heads

Revision ID: ac7f81a46a67
Revises: 96c981179643, add_oauth_users
Create Date: 2025-12-05 19:05:12.041903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac7f81a46a67'
down_revision: Union[str, Sequence[str], None] = ('96c981179643', 'add_oauth_users')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
