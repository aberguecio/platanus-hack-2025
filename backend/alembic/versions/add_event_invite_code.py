"""add event invite code

Revision ID: add_event_invite_code
Revises: bba933ec945e
Create Date: 2025-11-22 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_event_invite_code'
down_revision: Union[str, None] = 'bba933ec945e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add invite_code column to events table"""
    # Add invite_code column with a temporary default
    op.add_column('events', sa.Column('invite_code', sa.String(20), nullable=True))

    # Generate invite codes for existing events using Python
    from models import generate_invite_code
    connection = op.get_bind()
    events = connection.execute(sa.text("SELECT id FROM events")).fetchall()

    for event in events:
        invite_code = generate_invite_code()
        connection.execute(
            sa.text("UPDATE events SET invite_code = :code WHERE id = :id"),
            {"code": invite_code, "id": event[0]}
        )

    # Now make it NOT NULL and add constraints
    op.alter_column('events', 'invite_code', nullable=False)
    op.create_unique_constraint('uq_events_invite_code', 'events', ['invite_code'])
    op.create_index('ix_events_invite_code', 'events', ['invite_code'], unique=True)


def downgrade() -> None:
    """Remove invite_code column from events table"""
    op.drop_index('ix_events_invite_code', table_name='events')
    op.drop_constraint('uq_events_invite_code', 'events', type_='unique')
    op.drop_column('events', 'invite_code')
