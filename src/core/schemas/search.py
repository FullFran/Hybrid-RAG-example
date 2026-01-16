"""Domain schemas for search operations.

Contains domain value objects for search results.
DTOs like SearchResponse live in src/core/dtos/.
"""

from enum import Enum

from pydantic import BaseModel

from src.core.schemas.chunk import Chunk


class SearchType(Enum):
    """Type of search to perform."""

    SEMANTIC = "semantic"
    TEXT = "text"
    HYBRID = "hybrid"


class SearchHit(BaseModel):
    """A search result with explicit score types.

    Each score field is None if that search channel wasn't used.
    This prevents the "Frankenstein similarity" anti-pattern where
    one field means different things depending on context.
    """

    chunk: Chunk
    document_title: str
    document_source: str

    # Explicit scores - None if channel not used
    semantic_score: float | None = None
    text_score: float | None = None
    fusion_score: float | None = None

    @property
    def best_score(self) -> float:
        """Return the most relevant score available.

        Priority: fusion > semantic > text > 0.0
        """
        return self.fusion_score or self.semantic_score or self.text_score or 0.0


# Backwards compatibility alias (deprecated)
SearchMatch = SearchHit
