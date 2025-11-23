"""add image_description to memories

Revision ID: 204c6070933e
Revises: c7d8e9f0a1b2
Create Date: 2025-11-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '204c6070933e'
down_revision: Union[str, None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add image_description column to memories table
    op.add_column('memories', sa.Column('image_description', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove image_description column
    op.drop_column('memories', 'image_description')

