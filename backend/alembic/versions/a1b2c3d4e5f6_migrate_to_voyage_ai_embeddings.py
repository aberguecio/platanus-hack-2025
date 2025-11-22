"""migrate to voyage ai embeddings

Revision ID: a1b2c3d4e5f6
Revises: bba933ec945e
Create Date: 2025-11-22 12:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'bba933ec945e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old embedding column and recreate with new dimensions
    # Note: This will lose existing embedding data, but user specified to skip old memories
    op.drop_column('memories', 'embedding')
    op.add_column('memories', sa.Column('embedding', Vector(1024), nullable=True))

    # Create HNSW index for fast approximate nearest neighbor search
    # HNSW (Hierarchical Navigable Small World) is optimal for high-dimensional vectors
    # Using cosine distance (most common for embeddings) with reasonable performance parameters
    op.execute('''
        CREATE INDEX IF NOT EXISTS memories_embedding_idx
        ON memories
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    ''')


def downgrade() -> None:
    # Remove the HNSW index
    op.execute('DROP INDEX IF EXISTS memories_embedding_idx;')

    # Revert back to Vector(1536)
    op.drop_column('memories', 'embedding')
    op.add_column('memories', sa.Column('embedding', Vector(1536), nullable=True))
