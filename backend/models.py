from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid
from typing import List, Dict, Any

class DocumentMetadata(BaseModel):
    """Schema for tracking uploaded files in the database."""
    # We generate a unique ID for every document automatically
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    filename: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    total_chunks: int
    status: str = "indexed"


# 1. THE ACTION: What should the AI do?
class WorkflowAction(BaseModel):
    # This will be a string like "run_summary" or "run_quiz"
    type: str  
    # Optional extra data (e.g., {"target_language": "Spanish"})
    params: Optional[Dict[str, Any]] = None

# 2. THE CONDITION: Should we run this?
class WorkflowCondition(BaseModel):
    field: str      # We will check the "filename"
    operator: str   # We will check if it "contains"
    value: str      # The word "resume"

# 3. THE TEMPLATE: The complete automation saved in MongoDB
class WorkflowTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str       # "My Auto-Summarizer"
    trigger: str    # The event that starts this: "on_upload"
    conditions: List[WorkflowCondition] = []
    actions: List[WorkflowAction] = []

# 4. THE LOG: Proof that the automation ran successfully
class WorkflowLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    workflow_id: str
    document_id: str
    status: str      # "success" or "failed"
    output: Any      # The actual summary text returned by Gemini
    ran_at: datetime = Field(default_factory=datetime.utcnow)
