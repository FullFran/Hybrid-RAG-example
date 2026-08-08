from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Document(BaseModel):
    """Domain model for a source document."""

    id: str | None = Field(None, alias="_id")
    title: str
    source: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
