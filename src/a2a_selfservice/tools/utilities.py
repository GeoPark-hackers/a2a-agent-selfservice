"""Utility tools for common tasks."""

import json
from datetime import datetime, timezone

from .registry import register_tool


@register_tool()
def get_current_time(timezone_name: str = "UTC") -> str:
    """Get the current date and time.
    
    Args:
        timezone_name: Timezone name (currently only UTC supported)
    
    Returns:
        Current date and time as a formatted string.
    """
    now = datetime.now(timezone.utc)
    return f"Current time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}"


@register_tool()
def format_json(data: str) -> str:
    """Format a JSON string with proper indentation.
    
    Args:
        data: A JSON string to format
    
    Returns:
        Formatted JSON string.
    """
    try:
        parsed = json.loads(data)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"


@register_tool()
def text_length(text: str) -> str:
    """Count characters and words in text.
    
    Args:
        text: The text to analyze
    
    Returns:
        Character and word count.
    """
    char_count = len(text)
    word_count = len(text.split())
    return f"Characters: {char_count}, Words: {word_count}"


@register_tool()
def reverse_text(text: str) -> str:
    """Reverse a string.
    
    Args:
        text: The text to reverse
    
    Returns:
        The reversed text.
    """
    return text[::-1]
