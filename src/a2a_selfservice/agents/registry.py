"""Agent registry for managing created agents."""

from datetime import datetime
from typing import Any
from uuid import uuid4

import structlog
from google.adk.agents import Agent

from ..config import Settings, get_settings
from ..models import AgentDefinition, AgentResponse, AgentStatus
from ..storage.cosmos import CosmosDBStorage
from .base import BaseAgentFactory

logger = structlog.get_logger()


class AgentRegistry:
    """Registry for managing agent definitions and instances."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.factory = BaseAgentFactory(settings)
        self._agents: dict[str, Agent] = {}

        # Initialize Cosmos DB storage if configured
        self._storage: CosmosDBStorage | None = None
        if self.settings.cosmos_connection_string:
            try:
                self._storage = CosmosDBStorage(self.settings.cosmos_connection_string)
                logger.info("Using Cosmos DB for agent persistence")
            except Exception as e:
                logger.warning("Failed to initialize Cosmos DB, using in-memory", error=str(e))

        # In-memory fallback
        self._definitions: dict[str, AgentDefinition] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    async def register_agent(
        self,
        definition: AgentDefinition,
        deploy: bool = False,
    ) -> AgentResponse:
        """Register a new agent definition."""
        agent_id = str(uuid4())
        now = datetime.utcnow()

        # Save to Cosmos DB if available
        if self._storage:
            item = self._storage.save_agent(definition, agent_id, AgentStatus.DRAFT)
            logger.info("Agent registered to Cosmos DB", agent_name=definition.name)
        else:
            # Fallback to in-memory
            self._definitions[definition.name] = definition
            self._metadata[definition.name] = {
                "id": agent_id,
                "created_at": now,
                "updated_at": now,
                "status": AgentStatus.DRAFT,
            }
            logger.info("Agent registered in-memory", agent_name=definition.name)

        if deploy:
            await self.deploy_agent(definition.name)

        return await self._build_response(definition.name)

    async def deploy_agent(self, agent_name: str) -> AgentResponse:
        """Deploy an agent, making it available for invocation."""
        # Get definition from storage or memory
        definition = await self._get_definition(agent_name)
        if not definition:
            raise ValueError(f"Agent '{agent_name}' not found")

        # Update status to deploying
        if self._storage:
            self._storage.update_agent_status(agent_name, AgentStatus.DEPLOYING)
        else:
            self._metadata[agent_name]["status"] = AgentStatus.DEPLOYING
            self._metadata[agent_name]["updated_at"] = datetime.utcnow()

        try:
            sub_agents = []
            for sub_agent_name in definition.sub_agents:
                if sub_agent_name in self._agents:
                    sub_agents.append(self._agents[sub_agent_name])

            agent = self.factory.create_agent(definition, sub_agents)
            self._agents[agent_name] = agent

            # Update status to active
            if self._storage:
                self._storage.update_agent_status(agent_name, AgentStatus.ACTIVE)
            else:
                self._metadata[agent_name]["status"] = AgentStatus.ACTIVE
                self._metadata[agent_name]["a2a_endpoint"] = (
                    f"{self.settings.a2a_service_url}/api/v1/agents/{agent_name}/invoke"
                )
            logger.info("Agent deployed", agent_name=agent_name)

        except Exception as e:
            if self._storage:
                self._storage.update_agent_status(agent_name, AgentStatus.FAILED)
            else:
                self._metadata[agent_name]["status"] = AgentStatus.FAILED
                self._metadata[agent_name]["error"] = str(e)
            logger.error("Agent deployment failed", agent_name=agent_name, error=str(e))
            raise

        return await self._build_response(agent_name)

    async def get_agent(self, agent_name: str) -> AgentResponse:
        """Get agent information by name."""
        return await self._build_response(agent_name)

    async def list_agents(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[list[AgentResponse], int]:
        """List all registered agents."""
        if self._storage:
            items, total = self._storage.list_agents(page, page_size)
            responses = []
            for item in items:
                responses.append(await self._build_response_from_item(item))
            return responses, total
        else:
            agents = []
            for name in self._definitions:
                agents.append(await self._build_response(name))
            total = len(agents)
            start = (page - 1) * page_size
            end = start + page_size
            return agents[start:end], total

    async def delete_agent(self, agent_name: str) -> None:
        """Delete an agent."""
        if self._storage:
            if not self._storage.delete_agent(agent_name):
                raise ValueError(f"Agent '{agent_name}' not found")
        else:
            if agent_name not in self._definitions:
                raise ValueError(f"Agent '{agent_name}' not found")
            del self._definitions[agent_name]
            del self._metadata[agent_name]

        if agent_name in self._agents:
            del self._agents[agent_name]

        logger.info("Agent deleted", agent_name=agent_name)

    def get_agent_instance(self, agent_name: str) -> Agent | None:
        """Get the actual agent instance for invocation."""
        # If agent not in memory but exists in storage, deploy it first
        if agent_name not in self._agents and self._storage:
            item = self._storage.get_agent(agent_name)
            if item and item.get("status") == AgentStatus.ACTIVE.value:
                # Auto-deploy from storage
                definition = self._storage.to_definition(item)
                try:
                    agent = self.factory.create_agent(definition, [])
                    self._agents[agent_name] = agent
                    logger.info("Agent restored from Cosmos DB", agent_name=agent_name)
                except Exception as e:
                    logger.error("Failed to restore agent", agent_name=agent_name, error=str(e))
                    return None
        return self._agents.get(agent_name)

    async def _get_definition(self, agent_name: str) -> AgentDefinition | None:
        """Get agent definition from storage or memory."""
        if self._storage:
            item = self._storage.get_agent(agent_name)
            if item:
                return self._storage.to_definition(item)
            return None
        return self._definitions.get(agent_name)

    async def _build_response(self, agent_name: str) -> AgentResponse:
        """Build an AgentResponse from stored data."""
        if self._storage:
            item = self._storage.get_agent(agent_name)
            if not item:
                raise ValueError(f"Agent '{agent_name}' not found")
            return await self._build_response_from_item(item)
        else:
            if agent_name not in self._definitions:
                raise ValueError(f"Agent '{agent_name}' not found")
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

    async def _build_response_from_item(self, item: dict[str, Any]) -> AgentResponse:
        """Build an AgentResponse from a Cosmos DB item."""
        return AgentResponse(
            id=item["agent_id"],
            name=item["name"],
            display_name=item["display_name"],
            description=item["description"],
            status=AgentStatus(item["status"]),
            a2a_endpoint=f"{self.settings.a2a_service_url}/api/v1/agents/{item['name']}/invoke",
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            metadata=item.get("metadata", {}),
        )
