"""Data Transfer Objects for the RAG system.

DTOs are used to transfer data between layers (Application -> Endpoints).
They are NOT domain entities - those live in src/core/schemas/.
"""

from dataclasses import dataclass, field
from typing import Any

from src.core.schemas.search import SearchHit, SearchType


@dataclass
class SearchOptions:
    """Options for search operations.

    Allows per-query configuration of search behavior.
    Lives in Application layer, not Infrastructure.
    """

    threshold: float = 0.3
    filters: dict[str, Any] | None = None
    max_per_document: int | None = None  # For diversity


@dataclass
class SearchResponse:
    """Response from a search operation."""

    query: str
    hits: list[SearchHit]
    total_hits: int
    search_type: SearchType


@dataclass
class Citation:
    """A citation reference for transparency."""

    document_title: str
    document_source: str
    chunk_index: int


@dataclass
class ContextResult:
    """Result from context building with citations."""

    context: str
    citations: list[Citation] = field(default_factory=list)
    truncated: bool = False
