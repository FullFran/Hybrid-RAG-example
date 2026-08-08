from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class RawChunk:
    """Represents a chunk of document content before embedding."""

    content: str
    index: int
    metadata: dict[str, Any]
    token_count: int | None = None


class IChunker(ABC):
    """Interface for document chunking."""

    @abstractmethod
    async def chunk_document(
        self, content: str, title: str, source: str, docling_doc: Any | None = None
    ) -> list[RawChunk]:
        """
        Split a document into chunks.

        Args:
            content: Document content (markdown or text).
            title: Document title.
            source: Document source identifier.
            docling_doc: Optional raw document object from parser.

        Returns:
            List of RawChunk objects.
        """
