from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """Domain model for a document chunk.

    Represents a fragment of a document with its embedding and metadata.
    The id field is database-agnostic - transformations happen in repositories.
    """

    id: str | None = None
    document_id: str
    content: str
    embedding: list[float] | None = None
    chunk_index: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    token_count: int | None = None
    created_at: datetime = Field(default_factory=datetime.now)
