"""Core schemas for the RAG system.

Barrel exports for all domain models.
"""

from .chunk import Chunk
from .document import Document
from .search import SearchHit, SearchMatch, SearchType

__all__ = [
    "Chunk",
    "Document",
    "SearchHit",
    "SearchMatch",  # Deprecated alias for backwards compat
    "SearchType",
]
