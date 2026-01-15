"""merge framework v2 with main

Revision ID: 149a08bce4a4
Revises: 28772b1a241d, framework_v2_core
Create Date: 2025-12-12 21:43:26.596379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '149a08bce4a4'
down_revision: Union[str, Sequence[str], None] = ('28772b1a241d', 'framework_v2_core')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
