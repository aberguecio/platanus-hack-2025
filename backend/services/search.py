import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Memory, Event
from .embedding import EmbeddingService

logger = logging.getLogger(__name__)

#TODO: RM must use the model
class SearchResult:
    """Represents a search result with similarity score"""

    def __init__(self, memory: Memory, similarity_score: float):
        self.memory = memory
        self.similarity_score = similarity_score
        self.id = memory.id
        self.event_id = memory.event_id
        self.user_id = memory.user_id
        self.text = memory.text
        self.s3_url = memory.s3_url
        self.created_at = memory.created_at

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "text": self.text,
            "s3_url": self.s3_url,
            "similarity_score": round(self.similarity_score, 4),
            "similarity_percentage": round(self.similarity_score * 100, 2),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SearchService:
    """Service for semantic search using pgvector"""

    @staticmethod
    def search_memories(
        db: Session,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
        event_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Search memories by semantic similarity.

        Uses pgvector's cosine distance operator (<=> ) for efficient similarity search.
        The HNSW index created in the migration will automatically be used for performance.

        Args:
            db: Database session
            query: Search query text
            top_k: Maximum number of results to return
            threshold: Minimum similarity score (0-1), default 0 returns all
            event_id: Optional filter by event ID
            user_id: Optional filter by user ID

        Returns:
            List of SearchResult objects ordered by similarity (highest first)
        """
        try:
            # Generate query embedding
            query_embedding = EmbeddingService.embed_text(query, input_type="query")
            logger.info(f"Generated query embedding for: {query[:50]}...")

            # Build SQL query with pgvector cosine similarity
            # Note: pgvector's <=> operator returns distance (lower is better)
            # We convert to similarity: similarity = 1 - distance
            # Filter only memories that have embeddings

            sql = """
                SELECT
                    id,
                    event_id,
                    user_id,
                    text,
                    s3_url,
                    created_at,
                    1 - (embedding <=> :query_embedding) as similarity
                FROM memories
                WHERE embedding IS NOT NULL
            """

            params = {"query_embedding": str(query_embedding)}

            # Add optional filters
            if event_id is not None:
                sql += " AND event_id = :event_id"
                params["event_id"] = event_id

            if user_id is not None:
                sql += " AND user_id = :user_id"
                params["user_id"] = user_id

            # Add threshold filter
            if threshold > 0:
                sql += " AND (1 - (embedding <=> :query_embedding)) >= :threshold"
                params["threshold"] = threshold

            # Order by similarity and limit
            sql += " ORDER BY similarity DESC LIMIT :limit"
            params["limit"] = top_k

            # Execute query
            result = db.execute(text(sql), params)
            rows = result.fetchall()

            logger.info(f"Found {len(rows)} matching memories")

            # Convert to SearchResult objects
            search_results = []
            for row in rows:
                # Fetch the full Memory object for the result
                memory = db.query(Memory).filter(Memory.id == row.id).first()
                if memory:
                    similarity_score = float(row.similarity)
                    search_results.append(SearchResult(memory, similarity_score))

            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    @staticmethod
    def search_across_user_events(
        db: Session,
        user_id: int,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        Search across all events the user is part of.

        Args:
            db: Database session
            user_id: User ID to search for
            query: Search query text
            top_k: Maximum results
            threshold: Minimum similarity score

        Returns:
            List of SearchResult objects from all user's events
        """
        try:
            # Generate query embedding
            query_embedding = EmbeddingService.embed_text(query, input_type="query")

            # Query using pgvector similarity with join to user_events
            sql = """
                SELECT
                    m.id,
                    m.event_id,
                    m.user_id,
                    m.text,
                    m.s3_url,
                    m.created_at,
                    1 - (m.embedding <=> :query_embedding) as similarity
                FROM memories m
                INNER JOIN events e ON m.event_id = e.id
                INNER JOIN user_events ue ON e.id = ue.event_id
                WHERE ue.user_id = :user_id
                AND m.embedding IS NOT NULL
            """

            params = {
                "query_embedding": str(query_embedding),
                "user_id": user_id
            }

            # Add threshold
            if threshold > 0:
                sql += " AND (1 - (m.embedding <=> :query_embedding)) >= :threshold"
                params["threshold"] = threshold

            # Order and limit
            sql += " ORDER BY similarity DESC LIMIT :limit"
            params["limit"] = top_k

            result = db.execute(text(sql), params)
            rows = result.fetchall()

            logger.info(f"Found {len(rows)} matching memories across user's events")

            # Convert to SearchResult objects
            search_results = []
            for row in rows:
                memory = db.query(Memory).filter(Memory.id == row.id).first()
                if memory:
                    similarity_score = float(row.similarity)
                    search_results.append(SearchResult(memory, similarity_score))

            return search_results

        except Exception as e:
            logger.error(f"Cross-event search failed: {e}")
            raise

    @staticmethod
    def find_similar_memories(
        db: Session,
        memory_id: int,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[SearchResult]:
        """
        Find memories similar to a given memory.

        Useful for discovering related content.

        Args:
            db: Database session
            memory_id: ID of the memory to find similar items for
            top_k: Maximum results
            threshold: Minimum similarity (default 0.7 for relevance)

        Returns:
            List of similar memories (excluding the query memory itself)
        """
        try:
            # Get the source memory
            source_memory = db.query(Memory).filter(Memory.id == memory_id).first()

            if not source_memory or not source_memory.embedding:
                raise ValueError(f"Memory {memory_id} not found or has no embedding")

            # Query similar memories using pgvector
            sql = """
                SELECT
                    id,
                    event_id,
                    user_id,
                    text,
                    s3_url,
                    created_at,
                    1 - (embedding <=> :query_embedding) as similarity
                FROM memories
                WHERE id != :source_id
                AND embedding IS NOT NULL
                AND (1 - (embedding <=> :query_embedding)) >= :threshold
                ORDER BY similarity DESC
                LIMIT :limit
            """

            params = {
                "query_embedding": str(source_memory.embedding),
                "source_id": memory_id,
                "threshold": threshold,
                "limit": top_k
            }

            result = db.execute(text(sql), params)
            rows = result.fetchall()

            logger.info(f"Found {len(rows)} similar memories")

            # Convert to SearchResult objects
            search_results = []
            for row in rows:
                memory = db.query(Memory).filter(Memory.id == row.id).first()
                if memory:
                    similarity_score = float(row.similarity)
                    search_results.append(SearchResult(memory, similarity_score))

            return search_results

        except Exception as e:
            logger.error(f"Similar memories search failed: {e}")
            raise

    @staticmethod
    def get_search_statistics(db: Session) -> dict:
        """
        Get statistics about searchable memories.

        Returns:
            Dictionary with counts of memories with/without embeddings
        """
        try:
            total_memories = db.query(Memory).count()
            memories_with_embeddings = db.query(Memory).filter(
                Memory.embedding.isnot(None)
            ).count()
            memories_without_embeddings = total_memories - memories_with_embeddings

            return {
                "total_memories": total_memories,
                "searchable_memories": memories_with_embeddings,
                "unsearchable_memories": memories_without_embeddings,
                "coverage_percentage": round(
                    (memories_with_embeddings / total_memories * 100) if total_memories > 0 else 0,
                    2
                )
            }

        except Exception as e:
            logger.error(f"Failed to get search statistics: {e}")
            raise
