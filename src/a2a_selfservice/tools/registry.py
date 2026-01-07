"""Tool registry for mapping tool names to functions."""

from collections.abc import Callable
from typing import Any

# Global registry of tools
_TOOL_REGISTRY: dict[str, Callable[..., Any]] = {}


def register_tool(name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register a tool function.
    
    Usage:
        @register_tool()
        def my_tool(param: str) -> str:
            return "result"
        
        @register_tool("custom_name")
        def another_tool(param: str) -> str:
            return "result"
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or func.__name__
        _TOOL_REGISTRY[tool_name] = func
        return func
    return decorator


def get_tool(name: str) -> Callable[..., Any] | None:
    """Get a tool function by name."""
    return _TOOL_REGISTRY.get(name)


def list_tools() -> list[str]:
    """List all registered tool names."""
    return list(_TOOL_REGISTRY.keys())


def get_all_tools() -> dict[str, Callable[..., Any]]:
    """Get all registered tools."""
    return _TOOL_REGISTRY.copy()
