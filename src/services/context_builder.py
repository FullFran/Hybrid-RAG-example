"""Context builder for RAG responses.

Builds context strings from search hits with:
- Token/character limits
- Diversity (max chunks per document)
- Citation tracking
"""

import logging
from dataclasses import dataclass, field

from src.core.schemas.search import SearchHit

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """A citation reference for transparency."""

    document_title: str
    document_source: str
    chunk_index: int
    score: float


@dataclass
class ContextResult:
    """Result from context building."""

    context: str
    citations: list[Citation] = field(default_factory=list)
    truncated: bool = False
    total_hits: int = 0
    included_hits: int = 0


class ContextBuilder:
    """Builds context strings with limits and diversity.

    Prevents context explosion and ensures diverse sources.
    """

    def __init__(
        self,
        max_chars: int = 8000,
        max_per_document: int = 2,
    ):
        """Initialize context builder.

        Args:
            max_chars: Maximum characters in context.
            max_per_document: Maximum chunks from same document.
        """
        self.max_chars = max_chars
        self.max_per_document = max_per_document

    def build(self, hits: list[SearchHit]) -> ContextResult:
        """Build context from search hits.

        Args:
            hits: Search results, already sorted by relevance.

        Returns:
            ContextResult with context string and citations.
        """
        if not hits:
            return ContextResult(context="", total_hits=0, included_hits=0)

        doc_counts: dict[str, int] = {}
        context_parts: list[str] = []
        citations: list[Citation] = []
        current_chars = 0
        truncated = False

        for hit in hits:
            doc_id = hit.chunk.document_id

            # Enforce diversity: max chunks per document
            doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1
            if doc_counts[doc_id] > self.max_per_document:
                logger.debug(f"Skipping extra chunk from {hit.document_title}")
                continue

            # Format chunk
            chunk_text = (
                f"--- {hit.document_title} (chunk {hit.chunk.chunk_index}, "
                f"score: {hit.display_score:.3f}) ---\n{hit.chunk.content}"
            )

            # Check character limit
            if current_chars + len(chunk_text) > self.max_chars:
                truncated = True
                logger.debug(f"Context truncated at {current_chars} chars")
                break

            context_parts.append(chunk_text)
            current_chars += len(chunk_text) + 2  # +2 for newlines

            citations.append(
                Citation(
                    document_title=hit.document_title,
                    document_source=hit.document_source,
                    chunk_index=hit.chunk.chunk_index,
                    score=hit.display_score,
                )
            )

        return ContextResult(
            context="\n\n".join(context_parts),
            citations=citations,
            truncated=truncated,
            total_hits=len(hits),
            included_hits=len(citations),
        )
