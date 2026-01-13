from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """Domain model for a document chunk."""

    id: Optional[str] = Field(None, alias="_id")
    document_id: str
    content: str
    embedding: Optional[List[float]] = None
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    token_count: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
