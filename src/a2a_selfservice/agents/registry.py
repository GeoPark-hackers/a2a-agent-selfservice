"""Agent registry for managing created agents."""

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

import structlog

from google.adk.agents import Agent

from ..config import Settings, get_settings
from ..models import AgentDefinition, AgentResponse, AgentStatus
from .base import BaseAgentFactory

logger = structlog.get_logger()


class AgentRegistry:
    """Registry for managing agent definitions and instances."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.factory = BaseAgentFactory(settings)
        self._definitions: dict[str, AgentDefinition] = {}
        self._agents: dict[str, Agent] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    async def register_agent(
        self,
        definition: AgentDefinition,
        deploy: bool = False,
    ) -> AgentResponse:
        """Register a new agent definition."""
        agent_id = str(uuid4())
        now = datetime.utcnow()

        self._definitions[definition.name] = definition
        self._metadata[definition.name] = {
            "id": agent_id,
            "created_at": now,
            "updated_at": now,
            "status": AgentStatus.DRAFT,
        }

        logger.info("Agent registered", agent_name=definition.name, agent_id=agent_id)

        if deploy:
            await self.deploy_agent(definition.name)

        return self._build_response(definition.name)

    async def deploy_agent(self, agent_name: str) -> AgentResponse:
        """Deploy an agent, making it available for invocation."""
        if agent_name not in self._definitions:
            raise ValueError(f"Agent '{agent_name}' not found")

        definition = self._definitions[agent_name]
        self._metadata[agent_name]["status"] = AgentStatus.DEPLOYING
        self._metadata[agent_name]["updated_at"] = datetime.utcnow()

        try:
            sub_agents = []
            for sub_agent_name in definition.sub_agents:
                if sub_agent_name in self._agents:
                    sub_agents.append(self._agents[sub_agent_name])

            agent = self.factory.create_agent(definition, sub_agents)
            self._agents[agent_name] = agent

            self._metadata[agent_name]["status"] = AgentStatus.ACTIVE
            self._metadata[agent_name]["a2a_endpoint"] = (
                f"{self.settings.a2a_service_url}/api/v1/agents/{agent_name}/invoke"
            )
            logger.info("Agent deployed", agent_name=agent_name)

        except Exception as e:
            self._metadata[agent_name]["status"] = AgentStatus.FAILED
            self._metadata[agent_name]["error"] = str(e)
            logger.error("Agent deployment failed", agent_name=agent_name, error=str(e))
            raise

        return self._build_response(agent_name)

    async def get_agent(self, agent_name: str) -> AgentResponse:
        """Get agent information by name."""
        if agent_name not in self._definitions:
            raise ValueError(f"Agent '{agent_name}' not found")
        return self._build_response(agent_name)

    async def list_agents(self, page: int = 1, page_size: int = 10) -> tuple[list[AgentResponse], int]:
        """List all registered agents."""
        agents = [self._build_response(name) for name in self._definitions.keys()]
        total = len(agents)
        start = (page - 1) * page_size
        end = start + page_size
        return agents[start:end], total

    async def delete_agent(self, agent_name: str) -> None:
        """Delete an agent."""
        if agent_name not in self._definitions:
            raise ValueError(f"Agent '{agent_name}' not found")

        if agent_name in self._agents:
            del self._agents[agent_name]
        del self._definitions[agent_name]
        del self._metadata[agent_name]

        logger.info("Agent deleted", agent_name=agent_name)

    def get_agent_instance(self, agent_name: str) -> Agent | None:
        """Get the actual agent instance for invocation."""
        return self._agents.get(agent_name)

    def _build_response(self, agent_name: str) -> AgentResponse:
        """Build an AgentResponse from stored data."""
        definition = self._definitions[agent_name]
        metadata = self._metadata[agent_name]

        return AgentResponse(
            id=metadata["id"],
            name=definition.name,
            display_name=definition.display_name,
            description=definition.description,
            status=metadata["status"],
            a2a_endpoint=metadata.get("a2a_endpoint"),
            created_at=metadata["created_at"],
            updated_at=metadata["updated_at"],
            metadata=definition.metadata,
        )
