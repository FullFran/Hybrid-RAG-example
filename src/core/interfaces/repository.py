from abc import ABC, abstractmethod
from typing import List

from src.core.schemas.chunk import Chunk
from src.core.schemas.document import Document
from src.core.schemas.search import SearchMatch


class IRepository(ABC):
    """Interface for database persistence and retrieval."""

    @abstractmethod
    async def save_document(self, document: Document) -> str:
        """Save a document and return its ID."""
        pass

    @abstractmethod
    async def save_chunks(self, chunks: List[Chunk]) -> None:
        """Save a batch of document chunks."""
        pass

    @abstractmethod
    async def semantic_search(
        self, vector: List[float], limit: int
    ) -> List[SearchMatch]:
        """Perform semantic vector search."""
        pass

    @abstractmethod
    async def text_search(self, query: str, limit: int) -> List[SearchMatch]:
        """Perform full-text keyword search."""
        pass

    @abstractmethod
    async def clean_all(self) -> None:
        """Clear all documents and chunks."""
        pass
