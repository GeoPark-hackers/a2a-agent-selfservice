"""Base agent factory for creating ADK agents dynamically."""

from collections.abc import Callable
from typing import Any

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from ..config import Settings, get_settings
from ..models import AgentDefinition, ToolDefinition


class BaseAgentFactory:
    """Factory for creating ADK agents from definitions."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._model_config = self._get_model_config()

    def _get_model_config(self) -> dict[str, Any]:
        """Get model configuration based on provider."""
        import os

        if self.settings.llm_provider == "azure_openai":
            # Set environment variables for litellm Azure OpenAI
            os.environ["AZURE_API_KEY"] = self.settings.azure_openai_api_key
            os.environ["AZURE_API_BASE"] = self.settings.azure_openai_endpoint
            os.environ["AZURE_API_VERSION"] = self.settings.azure_openai_api_version
            return {
                "model": f"azure/{self.settings.azure_openai_deployment_name}",
            }
        else:
            return {
                "model": "gemini-2.0-flash",
            }

    def _create_tool_function(self, tool_def: ToolDefinition) -> Callable[..., Any]:
        """Create a callable function from a tool definition."""
        if tool_def.function_code:
            local_namespace: dict[str, Any] = {}
            exec(tool_def.function_code, local_namespace)
            func_name = tool_def.name
            if func_name in local_namespace:
                return local_namespace[func_name]

        async def placeholder_tool(**kwargs: Any) -> str:
            return f"Tool '{tool_def.name}' executed with parameters: {kwargs}"

        placeholder_tool.__name__ = tool_def.name
        placeholder_tool.__doc__ = tool_def.description
        return placeholder_tool

    def create_tools(self, tool_definitions: list[ToolDefinition]) -> list[FunctionTool]:
        """Create ADK tools from tool definitions."""
        tools = []
        for tool_def in tool_definitions:
            func = self._create_tool_function(tool_def)
            tool = FunctionTool(func=func)
            tools.append(tool)
        return tools

    def create_agent(
        self,
        definition: AgentDefinition,
        sub_agents: list[Agent] | None = None,
    ) -> Agent:
        """Create an ADK agent from a definition."""
        tools = self.create_tools(definition.tools)

        agent = Agent(
            name=definition.name,
            model=self._model_config.get("model", "gemini-2.0-flash"),
            instruction=definition.system_prompt,
            description=definition.description,
            tools=tools,
            sub_agents=sub_agents or [],
        )

        return agent
