"""merge narrative and video migrations

Revision ID: 187d44523ac0
Revises: 013eaac40ce6, d4b3ecc071bd
Create Date: 2025-11-23 09:55:43.986367

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '187d44523ac0'
down_revision: Union[str, None] = ('013eaac40ce6', 'd4b3ecc071bd')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
