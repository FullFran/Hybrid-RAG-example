from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class Document(BaseModel):
    """Domain model for a source document."""
    id: Optional[str] = Field(None, alias="_id")
    title: str
    source: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
