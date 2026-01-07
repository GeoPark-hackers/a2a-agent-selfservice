"""A2A protocol routes."""

from uuid import uuid4

import structlog
from fastapi import APIRouter, HTTPException, status
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from ..agents.registry import AgentRegistry
from ..config import get_settings
from .models import (
    AgentCard,
    Artifact,
    Message,
    MessageRole,
    Part,
    Skill,
    SkillParameter,
    Task,
    TaskCreateRequest,
    TaskSendMessageRequest,
    TaskState,
)

logger = structlog.get_logger(__name__)
router = APIRouter()

# Shared state
registry = AgentRegistry()
session_service = InMemorySessionService()
tasks: dict[str, Task] = {}  # In-memory task storage


def _get_base_url() -> str:
    """Get the base URL for A2A endpoints."""
    settings = get_settings()
    if settings.app_env == "production":
        return "https://a2a-selfservice.azurecontainerapps.io"
    return "https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io"


@router.get("/agents/{agent_name}/agent.json")
async def get_agent_card(agent_name: str) -> AgentCard:
    """Get the Agent Card for a specific agent.
    
    The Agent Card describes the agent's capabilities for discovery.
    """
    agent_response = await registry.get_agent(agent_name)
    if not agent_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )
    
    definition = await registry._get_definition(agent_name)
    
    # Build skills from tools
    skills = []
    if definition and definition.tools:
        for tool in definition.tools:
            params = []
            if tool.parameters and "properties" in tool.parameters:
                for param_name, param_info in tool.parameters["properties"].items():
                    params.append(SkillParameter(
                        name=param_name,
                        description=param_info.get("description", ""),
                        type=param_info.get("type", "string"),
                        required=param_name in tool.parameters.get("required", [])
                    ))
            
            skills.append(Skill(
                id=tool.name,
                name=tool.name,
                description=tool.description,
                parameters=params
            ))
    
    base_url = _get_base_url()
    
    return AgentCard(
        name=agent_name,
        description=agent_response.description,
        url=f"{base_url}/a2a/agents/{agent_name}",
        version="1.0.0",
        skills=skills,
        protocol_version="0.1",
        provider={
            "name": "A2A Self-Service Platform",
            "url": base_url
        },
        metadata={
            "display_name": agent_response.display_name,
            "status": agent_response.status.value,
        }
    )


@router.post("/agents/{agent_name}/tasks", response_model=Task)
async def create_task(agent_name: str, request: TaskCreateRequest) -> Task:
    """Create a new A2A task for an agent.
    
    This initiates a conversation with the agent.
    """
    agent = registry.get_agent_instance(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found or not deployed"
        )
    
    # Create task
    task_id = str(uuid4())
    session_id = request.session_id or str(uuid4())
    
    task = Task(
        id=task_id,
        session_id=session_id,
        state=TaskState.WORKING,
        messages=[request.message],
        metadata=request.metadata
    )
    
    try:
        # Create session
        session = await session_service.create_session(
            app_name="a2a-selfservice",
            user_id="default",
            session_id=session_id,
        )
        
        # Run agent
        runner = Runner(
            agent=agent,
            app_name="a2a-selfservice",
            session_service=session_service
        )
        
        # Extract text from message
        user_text = ""
        for part in request.message.parts:
            if part.text:
                user_text += part.text
        
        content = types.Content(
            role="user",
            parts=[types.Part(text=user_text)]
        )
        
        response_text = ""
        async for event in runner.run_async(
            user_id="default",
            session_id=session.id,
            new_message=content,
        ):
            if hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
            elif hasattr(event, "text") and event.text:
                response_text += event.text
        
        # Add agent response to task
        agent_message = Message(
            role=MessageRole.AGENT,
            parts=[Part(type="text", text=response_text)]
        )
        task.messages.append(agent_message)
        task.state = TaskState.COMPLETED
        
    except Exception as e:
        logger.error("Task failed", task_id=task_id, error=str(e))
        task.state = TaskState.FAILED
        task.metadata["error"] = str(e)
    
    # Store task
    tasks[task_id] = task
    
    return task


@router.get("/agents/{agent_name}/tasks/{task_id}", response_model=Task)
async def get_task(agent_name: str, task_id: str) -> Task:
    """Get the status of an A2A task."""
    if task_id not in tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found"
        )
    
    return tasks[task_id]


@router.post("/agents/{agent_name}/tasks/{task_id}/messages", response_model=Task)
async def send_message_to_task(
    agent_name: str,
    task_id: str,
    request: TaskSendMessageRequest
) -> Task:
    """Send a follow-up message to an existing task.
    
    This continues the conversation with the agent.
    """
    if task_id not in tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found"
        )
    
    task = tasks[task_id]
    
    if task.state in [TaskState.CANCELED, TaskState.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot send message to task in state '{task.state}'"
        )
    
    agent = registry.get_agent_instance(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found or not deployed"
        )
    
    # Add user message
    task.messages.append(request.message)
    task.state = TaskState.WORKING
    
    try:
        runner = Runner(
            agent=agent,
            app_name="a2a-selfservice",
            session_service=session_service
        )
        
        # Extract text from message
        user_text = ""
        for part in request.message.parts:
            if part.text:
                user_text += part.text
        
        content = types.Content(
            role="user",
            parts=[types.Part(text=user_text)]
        )
        
        response_text = ""
        async for event in runner.run_async(
            user_id="default",
            session_id=task.session_id,
            new_message=content,
        ):
            if hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
            elif hasattr(event, "text") and event.text:
                response_text += event.text
        
        # Add agent response
        agent_message = Message(
            role=MessageRole.AGENT,
            parts=[Part(type="text", text=response_text)]
        )
        task.messages.append(agent_message)
        task.state = TaskState.COMPLETED
        
    except Exception as e:
        logger.error("Task message failed", task_id=task_id, error=str(e))
        task.state = TaskState.FAILED
        task.metadata["error"] = str(e)
    
    return task


@router.post("/agents/{agent_name}/tasks/{task_id}/cancel")
async def cancel_task(agent_name: str, task_id: str) -> Task:
    """Cancel an A2A task."""
    if task_id not in tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found"
        )
    
    task = tasks[task_id]
    task.state = TaskState.CANCELED
    
    return task
