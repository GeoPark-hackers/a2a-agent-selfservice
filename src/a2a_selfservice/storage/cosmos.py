"""Cosmos DB storage for agent definitions."""

import json
from datetime import datetime
from typing import Any

import structlog
from azure.cosmos import CosmosClient, PartitionKey, exceptions

from ..config import get_settings
from ..models import AgentDefinition, AgentStatus

logger = structlog.get_logger()


class CosmosDBStorage:
    """Cosmos DB storage for agent definitions and metadata."""

    def __init__(self, connection_string: str | None = None):
        settings = get_settings()
        conn_str = connection_string or settings.cosmos_connection_string

        if not conn_str:
            raise ValueError("Cosmos DB connection string not configured")

        self.client = CosmosClient.from_connection_string(conn_str)
        self.database = self.client.get_database_client("agents")
        self.container = self.database.get_container_client("definitions")
        logger.info("Cosmos DB storage initialized")

    def save_agent(
        self,
        definition: AgentDefinition,
        agent_id: str,
        status: AgentStatus = AgentStatus.DRAFT,
    ) -> dict[str, Any]:
        """Save agent definition to Cosmos DB."""
        now = datetime.utcnow().isoformat()

        item = {
            "id": definition.name,
            "name": definition.name,
            "agent_id": agent_id,
            "display_name": definition.display_name,
            "description": definition.description,
            "system_prompt": definition.system_prompt,
            "model": definition.model,
            "tools": [tool.model_dump() for tool in definition.tools],
            "sub_agents": definition.sub_agents,
            "metadata": definition.metadata,
            "status": status.value,
            "created_at": now,
            "updated_at": now,
        }

        try:
            self.container.upsert_item(item)
            logger.info("Agent saved to Cosmos DB", agent_name=definition.name)
            return item
        except exceptions.CosmosHttpResponseError as e:
            logger.error("Failed to save agent", agent_name=definition.name, error=str(e))
            raise

    def get_agent(self, name: str) -> dict[str, Any] | None:
        """Get agent definition from Cosmos DB."""
        try:
            item = self.container.read_item(item=name, partition_key=name)
            return item
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error("Failed to get agent", agent_name=name, error=str(e))
            raise

    def update_agent_status(self, name: str, status: AgentStatus) -> dict[str, Any] | None:
        """Update agent status in Cosmos DB."""
        item = self.get_agent(name)
        if not item:
            return None

        item["status"] = status.value
        item["updated_at"] = datetime.utcnow().isoformat()

        try:
            self.container.upsert_item(item)
            logger.info("Agent status updated", agent_name=name, status=status.value)
            return item
        except exceptions.CosmosHttpResponseError as e:
            logger.error("Failed to update agent status", agent_name=name, error=str(e))
            raise

    def delete_agent(self, name: str) -> bool:
        """Delete agent from Cosmos DB."""
        try:
            self.container.delete_item(item=name, partition_key=name)
            logger.info("Agent deleted from Cosmos DB", agent_name=name)
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
        except exceptions.CosmosHttpResponseError as e:
            logger.error("Failed to delete agent", agent_name=name, error=str(e))
            raise

    def list_agents(self, page: int = 1, page_size: int = 10) -> tuple[list[dict[str, Any]], int]:
        """List all agents from Cosmos DB with pagination."""
        try:
            query = "SELECT * FROM c ORDER BY c.created_at DESC"
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
            total = len(items)

            start = (page - 1) * page_size
            end = start + page_size
            paginated = items[start:end]

            return paginated, total
        except exceptions.CosmosHttpResponseError as e:
            logger.error("Failed to list agents", error=str(e))
            raise

    def to_definition(self, item: dict[str, Any]) -> AgentDefinition:
        """Convert Cosmos DB item to AgentDefinition."""
        from ..models import ToolDefinition

        return AgentDefinition(
            name=item["name"],
            display_name=item["display_name"],
            description=item["description"],
            system_prompt=item["system_prompt"],
            model=item.get("model", "gpt-4o"),
            tools=[ToolDefinition(**t) for t in item.get("tools", [])],
            sub_agents=item.get("sub_agents", []),
            metadata=item.get("metadata", {}),
        )
