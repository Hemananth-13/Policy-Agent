from pydantic import BaseModel, Field
from typing import List, Optional


# ── Custom exception hierarchy ─────────────────────────────────────────────────

class AgentError(Exception):
    """Raised when the agent loop fails."""
    pass

class LLMError(AgentError):
    """Raised when an LLM API call fails after all retries."""
    pass

class DocumentError(AgentError):
    """Raised when document generation or saving fails."""
    pass


# ── Pydantic models ────────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    request: str = Field(..., description="Natural language insurance policy request")


class TaskItem(BaseModel):
    task_id: int
    task_name: str
    status: str = "pending"  # pending | completed | failed
    result: Optional[str] = Field(default=None, exclude=True)  # excluded from API response


class ReflectionNote(BaseModel):
    passed: bool
    issues_found: List[str]
    improvements_made: List[str]


class AgentResponse(BaseModel):
    request: str
    tasks: List[TaskItem]
    reflection: ReflectionNote
    document_path: str
    download_url: str
    message: str
