"""Pydantic models for the A2A Self-Service API."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Status of an agent."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPLOYING = "deploying"
    FAILED = "failed"


class ToolDefinition(BaseModel):
    """Definition of a tool that an agent can use."""

    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for parameters"
    )
    function_code: str | None = Field(default=None, description="Python code for the tool function")


class AgentDefinition(BaseModel):
    """Definition of an agent to be created."""

    name: str = Field(..., description="Unique name for the agent")
    display_name: str = Field(..., description="Human-readable display name")
    description: str = Field(..., description="Description of the agent's purpose")
    system_prompt: str = Field(..., description="System prompt/instructions for the agent")
    model: str = Field(default="gpt-4o", description="Model to use for the agent")
    tools: list[ToolDefinition] = Field(
        default_factory=list, description="Tools available to the agent"
    )
    sub_agents: list[str] = Field(
        default_factory=list, description="Sub-agents this agent can delegate to"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentCreateRequest(BaseModel):
    """Request to create a new agent."""

    definition: AgentDefinition
    deploy_immediately: bool = Field(
        default=False, description="Whether to deploy the agent immediately"
    )


class AgentResponse(BaseModel):
    """Response containing agent information."""

    id: str
    name: str
    display_name: str
    description: str
    status: AgentStatus
    a2a_endpoint: str | None = None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentListResponse(BaseModel):
    """Response containing a list of agents."""

    agents: list[AgentResponse]
    total: int
    page: int = 1
    page_size: int = 10


class AgentInvokeRequest(BaseModel):
    """Request to invoke an agent."""

    message: str = Field(..., description="Message to send to the agent")
    session_id: str | None = Field(
        default=None, description="Session ID for conversation continuity"
    )
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class AgentInvokeResponse(BaseModel):
    """Response from invoking an agent."""

    response: str
    session_id: str
    agent_name: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
