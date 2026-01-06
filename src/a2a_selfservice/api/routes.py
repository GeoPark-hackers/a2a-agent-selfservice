"""API routes for agent management and invocation."""

from datetime import datetime
from uuid import uuid4

import structlog
from fastapi import APIRouter, HTTPException, status
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .. import __version__
from ..agents.registry import AgentRegistry
from ..config import get_settings
from ..models import (
    AgentCreateRequest,
    AgentInvokeRequest,
    AgentInvokeResponse,
    AgentListResponse,
    AgentResponse,
    HealthResponse,
)

logger = structlog.get_logger()
router = APIRouter()

registry = AgentRegistry()
session_service = InMemorySessionService()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=__version__,
        environment=settings.app_env,
        timestamp=datetime.utcnow(),
    )


@router.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(request: AgentCreateRequest) -> AgentResponse:
    """Create a new agent from a definition."""
    try:
        response = await registry.register_agent(
            definition=request.definition,
            deploy=request.deploy_immediately,
        )
        logger.info("Agent created", agent_name=request.definition.name)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
    except Exception as e:
        logger.error("Failed to create agent", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/agents", response_model=AgentListResponse)
async def list_agents(page: int = 1, page_size: int = 10) -> AgentListResponse:
    """List all registered agents."""
    agents, total = await registry.list_agents(page=page, page_size=page_size)
    return AgentListResponse(agents=agents, total=total, page=page, page_size=page_size)


@router.get("/agents/{agent_name}", response_model=AgentResponse)
async def get_agent(agent_name: str) -> AgentResponse:
    """Get agent details by name."""
    try:
        return await registry.get_agent(agent_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


@router.post("/agents/{agent_name}/deploy", response_model=AgentResponse)
async def deploy_agent(agent_name: str) -> AgentResponse:
    """Deploy an agent, making it available for invocation."""
    try:
        return await registry.deploy_agent(agent_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None
    except Exception as e:
        logger.error("Failed to deploy agent", agent_name=agent_name, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.delete("/agents/{agent_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_name: str) -> None:
    """Delete an agent."""
    try:
        await registry.delete_agent(agent_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


@router.post("/agents/{agent_name}/invoke", response_model=AgentInvokeResponse)
async def invoke_agent(agent_name: str, request: AgentInvokeRequest) -> AgentInvokeResponse:
    """Invoke an agent with a message."""
    agent = registry.get_agent_instance(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found or not deployed",
        )

    try:
        # Create or get session (ADK session methods are async)
        if request.session_id:
            session = await session_service.get_session(
                app_name="a2a-selfservice",
                user_id="default",
                session_id=request.session_id,
            )
            if not session:
                session = await session_service.create_session(
                    app_name="a2a-selfservice",
                    user_id="default",
                    session_id=request.session_id,
                )
        else:
            session = await session_service.create_session(
                app_name="a2a-selfservice",
                user_id="default",
            )

        runner = Runner(
            agent=agent, app_name="a2a-selfservice", session_service=session_service
        )

        # Format message as Content object expected by ADK
        content = types.Content(
            role="user", parts=[types.Part(text=request.message)]
        )

        response_text = ""
        async for event in runner.run_async(
            user_id="default",
            session_id=session.id,
            new_message=content,
        ):
            logger.debug("ADK event received", event_type=type(event).__name__, event=str(event)[:200])
            # Check for content in different event attributes
            if hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
            elif hasattr(event, "text") and event.text:
                response_text += event.text

        return AgentInvokeResponse(
            response=response_text,
            session_id=session.id,
            agent_name=agent_name,
            metadata=request.context,
        )

    except Exception as e:
        logger.error("Failed to invoke agent", agent_name=agent_name, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
