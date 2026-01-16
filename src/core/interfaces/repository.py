"""Repository interface for database persistence and retrieval.

This module defines the abstract interface that all database implementations
must follow. Implementations can use MongoDB, PostgreSQL/pgvector, or any
other database that supports vector search.
"""

from abc import ABC, abstractmethod
from typing import List

from src.core.schemas.chunk import Chunk
from src.core.schemas.document import Document
from src.core.schemas.search import SearchHit


class IRepository(ABC):
    """Interface for database persistence and retrieval.

    All methods are async to allow non-blocking I/O operations.
    Implementations should handle connection management internally.
    """

    @abstractmethod
    async def save_document(self, document: Document) -> str:
        """Save a document and return its ID.

        Args:
            document: The document to save. The id field may be None
                     for new documents.

        Returns:
            The ID of the saved document (generated if not provided).

        Raises:
            DocumentSaveError: If the document fails to save.
        """
        pass

    @abstractmethod
    async def save_chunks(self, chunks: List[Chunk]) -> None:
        """Save a batch of document chunks.

        Args:
            chunks: List of chunks to save. Should belong to the same document.

        Raises:
            ChunkSaveError: If chunks fail to save.
        """
        pass

    @abstractmethod
    async def semantic_search(
        self, vector: List[float], limit: int, threshold: float | None = None
    ) -> List[SearchHit]:
        """Perform semantic vector search.

        Args:
            vector: Query embedding vector.
            limit: Maximum number of results to return.
            threshold: Optional similarity threshold override.

        Returns:
            List of SearchHit with semantic_score populated.
            Sorted by relevance (descending). Empty if no matches.

        Raises:
            SearchError: If database query fails.
        """
        pass

    @abstractmethod
    async def text_search(self, query: str, limit: int) -> List[SearchHit]:
        """Perform full-text keyword search.

        Args:
            query: The text query to search for.
            limit: Maximum number of results to return.

        Returns:
            List of SearchHit with text_score populated.
            Sorted by relevance (descending). Empty if no matches.

        Raises:
            SearchError: If database query fails.
        """
        pass

    @abstractmethod
    async def clean_all(self) -> None:
        """Clear all documents and chunks.

        Use with caution - this operation is irreversible.
        Typically used for testing or resetting the database.

        Raises:
            RepositoryError: If cleanup fails.
        """
        pass
