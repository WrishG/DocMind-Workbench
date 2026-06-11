from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class DocumentMetadata(BaseModel):
    """Schema for tracking uploaded files in the database."""
    # We generate a unique ID for every document automatically
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    filename: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    total_chunks: int
    status: str = "indexed"
