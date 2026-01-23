from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RawChunk:
    """Represents a chunk of document content before embedding."""

    content: str
    index: int
    metadata: Dict[str, Any]
    token_count: Optional[int] = None


class IChunker(ABC):
    """Interface for document chunking."""

    @abstractmethod
    async def chunk_document(
        self, content: str, title: str, source: str, docling_doc: Optional[Any] = None
    ) -> List[RawChunk]:
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
        pass
