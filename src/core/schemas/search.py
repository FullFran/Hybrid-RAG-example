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
    def display_score(self) -> float:
        """Return the most relevant score available for display purposes.

        Priority: fusion > semantic > text > 0.0
        Note: Use explicit score fields for business logic decision making.
        """
        if self.fusion_score is not None:
            return self.fusion_score
        if self.semantic_score is not None:
            return self.semantic_score
        if self.text_score is not None:
            return self.text_score
        return 0.0


# DEPRECATED: Use SearchHit instead. Kept for minimal backwards compatibility.
SearchMatch = SearchHit
