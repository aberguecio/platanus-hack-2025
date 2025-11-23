"""merge photo and invite code migrations

Revision ID: 484ffb5c5a2e
Revises: eada2497970c, ff168deb9a00
Create Date: 2025-11-23 00:56:34.468842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '484ffb5c5a2e'
down_revision: Union[str, None] = ('eada2497970c', 'ff168deb9a00')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
