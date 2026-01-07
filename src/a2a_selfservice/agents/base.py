"""Base agent factory for creating ADK agents dynamically."""

import os
from collections.abc import Callable
from typing import Any

import structlog
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

from ..config import Settings, get_settings
from ..models import AgentDefinition, ToolDefinition
from ..tools import get_tool

logger = structlog.get_logger(__name__)


class BaseAgentFactory:
    """Factory for creating ADK agents from definitions."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._setup_environment()

    def _setup_environment(self) -> None:
        """Set up environment variables for LLM providers."""
        if self.settings.llm_provider == "azure_openai":
            # Set environment variables for litellm Azure OpenAI
            os.environ["AZURE_API_KEY"] = self.settings.azure_openai_api_key
            os.environ["AZURE_API_BASE"] = self.settings.azure_openai_endpoint
            os.environ["AZURE_API_VERSION"] = self.settings.azure_openai_api_version

    def _get_model(self) -> LiteLlm | str:
        """Get model instance based on provider."""
        if self.settings.llm_provider == "azure_openai":
            # Use LiteLlm wrapper for Azure OpenAI
            return LiteLlm(model=f"azure/{self.settings.azure_openai_deployment_name}")
        else:
            # Use Gemini model directly (native to ADK)
            return "gemini-2.0-flash"

    def _get_tool_function(self, tool_def: ToolDefinition) -> Callable[..., Any] | None:
        """Get a tool function from the repository registry.
        
        Tools must be defined in the repository under src/a2a_selfservice/tools/
        and registered using the @register_tool() decorator.
        """
        # Look up tool in repository registry
        func = get_tool(tool_def.name)
        if func:
            logger.debug("Found tool in registry", tool_name=tool_def.name)
            return func
        
        logger.warning("Tool not found in registry", tool_name=tool_def.name)
        return None

    def create_tools(self, tool_definitions: list[ToolDefinition]) -> list[FunctionTool]:
        """Create ADK tools from tool definitions.
        
        Tools are looked up from the repository registry. Only tools defined
        in the codebase and registered with @register_tool() will work.
        """
        tools = []
        for tool_def in tool_definitions:
            func = self._get_tool_function(tool_def)
            if func:
                tool = FunctionTool(func=func)
                tools.append(tool)
            else:
                logger.error(
                    "Skipping unknown tool - must be defined in repository",
                    tool_name=tool_def.name
                )
        return tools

    def create_agent(
        self,
        definition: AgentDefinition,
        sub_agents: list[Agent] | None = None,
    ) -> Agent:
        """Create an ADK agent from a definition."""
        tools = self.create_tools(definition.tools)
        model = self._get_model()

        agent = Agent(
            name=definition.name,
            model=model,
            instruction=definition.system_prompt,
            description=definition.description,
            tools=tools,
            sub_agents=sub_agents or [],
        )

        return agent
