from typing import List

from pydantic import BaseModel

from src.core.schemas.chunk import Chunk


class SearchMatch(BaseModel):
    """Represents a chunk retrieved during search with its relevance score."""

    chunk: Chunk
    similarity: float
    document_title: str
    document_source: str


class SearchResponse(BaseModel):
    """Unified response for search operations."""

    query: str
    matches: List[SearchMatch]
    total_matches: int
    search_type: str  # 'semantic', 'text', 'hybrid'
