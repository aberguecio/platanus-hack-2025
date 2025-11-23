import os
import time
import logging
from typing import List, Literal
import voyageai

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using Voyage AI"""

    _client = None
    _model = "voyage-2" #"voyage-3-large" # "voyage-2"

    @classmethod
    def _get_client(cls) -> voyageai.Client:
        """Get or initialize Voyage AI client"""
        if cls._client is None:
            api_key = os.getenv("VOYAGE_API_KEY")
            if not api_key:
                raise ValueError("VOYAGE_API_KEY environment variable not set")
            cls._client = voyageai.Client(api_key=api_key)
        return cls._client

    @staticmethod
    def _preprocess_text(text: str) -> str:
        """Clean and preprocess text for embedding"""
        if not text:
            return ""

        # Remove excessive whitespace
        text = " ".join(text.split())

        # Trim to reasonable length (Voyage AI has token limits)
        # Roughly 4 chars per token, limit to ~16k tokens
        max_chars = 64000
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters for embedding")

        return text

    @classmethod
    def embed_text(
        cls,
        text: str,
        input_type: Literal["document", "query"] = "document",
        retry_attempts: int = 3,
        retry_delay: float = 1.0
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            input_type: "document" for storing, "query" for searching
            retry_attempts: Number of retry attempts on failure
            retry_delay: Initial delay between retries (exponential backoff)

        Returns:
            List of 1024 floats representing the embedding vector

        Raises:
            ValueError: If text is empty or API key not set
            Exception: If API call fails after retries
        """
        text = cls._preprocess_text(text)

        if not text:
            raise ValueError("Cannot embed empty text")

        client = cls._get_client()

        for attempt in range(retry_attempts):
            try:
                result = client.embed(
                    texts=[text],
                    model=cls._model,
                    input_type=input_type
                )

                # Extract the embedding vector
                embedding = result.embeddings[0]

                logger.info(f"Generated {input_type} embedding with {len(embedding)} dimensions")
                return embedding

            except Exception as e:
                error_msg = str(e).lower()

                # Check for rate limiting
                if "rate limit" in error_msg or "429" in error_msg:
                    if attempt < retry_attempts - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{retry_attempts}")
                        time.sleep(wait_time)
                        continue

                # Check for other retryable errors
                if "timeout" in error_msg or "connection" in error_msg:
                    if attempt < retry_attempts - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Connection error, retrying {attempt + 1}/{retry_attempts}")
                        time.sleep(wait_time)
                        continue

                # Non-retryable error or final attempt
                logger.error(f"Failed to generate embedding: {e}")
                raise

    @classmethod
    def embed_texts_batch(
        cls,
        texts: List[str],
        input_type: Literal["document", "query"] = "document",
        batch_size: int = 128
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Voyage AI supports up to 128 texts per request for better efficiency.

        Args:
            texts: List of texts to embed
            input_type: "document" for storing, "query" for searching
            batch_size: Number of texts per API call (max 128)

        Returns:
            List of embedding vectors (each is List[float] of length 1024)
        """
        if not texts:
            return []

        # Preprocess all texts
        processed_texts = [cls._preprocess_text(text) for text in texts]

        # Filter out empty texts
        valid_texts = [t for t in processed_texts if t]

        if not valid_texts:
            raise ValueError("No valid texts to embed after preprocessing")

        client = cls._get_client()
        embeddings = []

        # Process in batches
        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]

            try:
                result = client.embed(
                    texts=batch,
                    model=cls._model,
                    input_type=input_type
                )
                embeddings.extend(result.embeddings)

                logger.info(f"Generated {len(batch)} embeddings in batch (batch {i//batch_size + 1})")

            except Exception as e:
                logger.error(f"Failed to generate batch embeddings: {e}")
                raise

        return embeddings

    @classmethod
    def get_embedding_dimensions(cls) -> int:
        """Get the dimensionality of embeddings from this model"""
        return 1024  # voyage-2 produces 1024-dimensional embeddings
