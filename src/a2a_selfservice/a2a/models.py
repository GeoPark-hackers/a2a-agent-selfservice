"""A2A protocol models based on the A2A specification."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskState(str, Enum):
    """State of an A2A task."""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"


class MessageRole(str, Enum):
    """Role of a message sender."""
    USER = "user"
    AGENT = "agent"


class Part(BaseModel):
    """A part of a message content."""
    type: str = "text"
    text: str | None = None
    data: str | None = None  # Base64 encoded for files
    mime_type: str | None = None


class Message(BaseModel):
    """A message in an A2A conversation."""
    role: MessageRole
    parts: list[Part]
    metadata: dict[str, Any] = Field(default_factory=dict)


class Artifact(BaseModel):
    """An artifact produced by an agent."""
    id: str
    name: str
    mime_type: str
    data: str  # Base64 encoded
    metadata: dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    """An A2A task representing a unit of work."""
    id: str
    session_id: str | None = None
    state: TaskState = TaskState.SUBMITTED
    messages: list[Message] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskCreateRequest(BaseModel):
    """Request to create a new task."""
    message: Message
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskSendMessageRequest(BaseModel):
    """Request to send a message to an existing task."""
    message: Message


class SkillParameter(BaseModel):
    """A parameter for a skill."""
    name: str
    description: str | None = None
    type: str = "string"
    required: bool = False


class Skill(BaseModel):
    """A skill (capability) of an agent."""
    id: str
    name: str
    description: str | None = None
    parameters: list[SkillParameter] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentCard(BaseModel):
    """Agent Card - describes an agent's capabilities for discovery.
    
    This follows the A2A specification for agent discovery.
    """
    name: str
    description: str | None = None
    url: str  # Base URL for A2A endpoints
    version: str = "1.0.0"
    
    # Capabilities
    skills: list[Skill] = Field(default_factory=list)
    
    # Protocol support
    protocol_version: str = "0.1"
    
    # Authentication (optional)
    authentication: dict[str, Any] | None = None
    
    # Additional metadata
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    # Provider info
    provider: dict[str, str] | None = None


class AgentCardResponse(BaseModel):
    """Response wrapper for agent card."""
    agent: AgentCard
