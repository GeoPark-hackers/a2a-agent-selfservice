# Building Agents and Tools

This guide explains how to create agents, define tools, and how agents use tools in the A2A Self-Service platform.

## Table of Contents

- [Creating an Agent](#creating-an-agent)
- [Available Tools](#available-tools)
- [Adding New Tools](#adding-new-tools)
- [How Agents Use Tools](#how-agents-use-tools)
- [Examples](#examples)
- [API Reference](#api-reference)

---

## Creating an Agent

Agents are AI assistants that can answer questions and perform tasks. Each agent has:

- **name**: Unique identifier (must be a valid Python identifier - no hyphens, use underscores)
- **display_name**: Human-readable name
- **description**: What the agent does
- **system_prompt**: Instructions that define the agent's behavior
- **tools**: List of tools the agent can use (optional)

### Basic Agent (No Tools)

```bash
curl -X POST https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "definition": {
      "name": "general_assistant",
      "display_name": "General Assistant",
      "description": "A helpful general-purpose assistant",
      "system_prompt": "You are a helpful assistant. Answer questions clearly and concisely.",
      "tools": []
    },
    "deploy_immediately": true
  }'
```

### Agent with Tools

Tools are pre-defined in the repository. Reference them by name:

```bash
curl -X POST https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "definition": {
      "name": "calculator_agent",
      "display_name": "Calculator Agent",
      "description": "An agent that can perform calculations",
      "system_prompt": "You are a math assistant. Use the calculate tool for math expressions, or add/subtract/multiply/divide for basic operations.",
      "tools": [
        {"name": "calculate", "description": "Evaluate math expressions"},
        {"name": "add", "description": "Add two numbers"},
        {"name": "subtract", "description": "Subtract two numbers"},
        {"name": "convert_units", "description": "Convert between units"}
      ]
    },
    "deploy_immediately": true
  }'
```

---

## Available Tools

Tools are pre-defined in the repository for security and control. To see all available tools:

```bash
curl https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/api/v1/tools
```

### Calculator Tools

| Tool | Description |
|------|-------------|
| `calculate` | Evaluate mathematical expressions safely (e.g., "2 + 2", "sqrt(16)") |
| `add` | Add two numbers |
| `subtract` | Subtract two numbers |
| `multiply` | Multiply two numbers |
| `divide` | Divide two numbers |
| `convert_units` | Convert between units (km/miles, celsius/fahrenheit, kg/lbs) |

### Weather Tools

| Tool | Description |
|------|-------------|
| `get_weather` | Get current weather for a city |
| `get_forecast` | Get weather forecast for a city |

### Utility Tools

| Tool | Description |
|------|-------------|
| `get_current_time` | Get current date and time (UTC) |
| `format_json` | Format a JSON string with indentation |
| `text_length` | Count characters and words in text |
| `reverse_text` | Reverse a string |

---

## Adding New Tools

Tools are defined in the repository under `src/a2a_selfservice/tools/`. This approach provides:

- ✅ **Security** - No arbitrary code execution
- ✅ **Version control** - Tools are tracked in git
- ✅ **Testing** - Tools can be unit tested
- ✅ **Full Python** - Access to any package or API

### Step 1: Create a Tool File

Create a new file in `src/a2a_selfservice/tools/`:

```python
# src/a2a_selfservice/tools/my_tools.py
"""My custom tools."""

from .registry import register_tool


@register_tool()
def my_tool(param1: str, param2: int = 10) -> str:
    """Short description of what this tool does.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
    
    Returns:
        A string with the result.
    """
    # Your implementation here
    result = f"Processed {param1} with value {param2}"
    return result
```

### Step 2: Register the Module

Add your module to `src/a2a_selfservice/tools/__init__.py`:

```python
from . import my_tools  # noqa: F401
```

### Step 3: Deploy

Commit, push, and deploy. The new tool will be available to all agents.

### Tool Guidelines

- **Use type hints** - Parameters and return types should be typed
- **Write docstrings** - The first line becomes the tool description for the LLM
- **Return strings** - Tools should return human-readable strings
- **Handle errors** - Catch exceptions and return helpful error messages
- **Keep focused** - Each tool should do one thing well

---

## How Agents Use Tools

1. **User sends a message** to the agent
2. **LLM analyzes** the message and decides if a tool is needed
3. **If tool needed**, the LLM generates a tool call with parameters
4. **Tool executes** and returns a result
5. **LLM incorporates** the tool result into its response
6. **User receives** the final response

### System Prompt Best Practices

The system prompt should guide the agent on when to use tools:

```
You are a helpful assistant with access to the following tools:
- calculate: Use this for any mathematical calculations
- get_weather: Use this when users ask about weather

When a user asks a question that requires one of these tools, use the appropriate tool to get the answer. Always explain the result clearly.
```

---

## Examples

### 1. Weather Agent

```bash
curl -X POST https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "definition": {
      "name": "weather_agent",
      "display_name": "Weather Agent",
      "description": "An agent that provides weather information",
      "system_prompt": "You are a weather assistant. Use get_weather for current conditions and get_forecast for multi-day forecasts.",
      "tools": [
        {"name": "get_weather", "description": "Get current weather for a city"},
        {"name": "get_forecast", "description": "Get weather forecast for a city"}
      ]
    },
    "deploy_immediately": true
  }'
```

### 2. Multi-Tool Utility Agent

```bash
curl -X POST https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "definition": {
      "name": "utility_agent",
      "display_name": "Utility Agent",
      "description": "An agent with multiple utility tools",
      "system_prompt": "You are a utility assistant. Available tools:\n- calculate: for math expressions\n- convert_units: for unit conversions\n- get_current_time: for current time\n- text_length: to count characters/words",
      "tools": [
        {"name": "calculate", "description": "Evaluate math expressions"},
        {"name": "convert_units", "description": "Convert between units"},
        {"name": "get_current_time", "description": "Get current time"},
        {"name": "text_length", "description": "Count characters and words"}
      ]
    },
    "deploy_immediately": true
  }'
```

### 3. Invoke an Agent with Tools

```bash
curl -X POST https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/api/v1/agents/utility_agent/invoke \
  -H "Content-Type: application/json" \
  -d '{"message": "Convert 100 kilometers to miles"}'
```

Response:
```json
{
  "response": "100 km = 62.1371 miles",
  "session_id": "abc123",
  "agent_name": "utility_agent"
}
```

---

## API Reference

### List Available Tools

```
GET /api/v1/tools
```

**Response:**
```json
{
  "tools": [
    {"name": "calculate", "description": "Evaluate a mathematical expression safely."},
    {"name": "get_weather", "description": "Get the current weather for a city."}
  ],
  "count": 2
}
```

### Create Agent

```
POST /api/v1/agents
```

**Request Body:**
```json
{
  "definition": {
    "name": "string (required)",
    "display_name": "string (optional)",
    "description": "string (optional)",
    "system_prompt": "string (required)",
    "tools": [
      {
        "name": "string (required - must match a registered tool)",
        "description": "string (optional - override for LLM context)"
      }
    ]
  },
  "deploy_immediately": true
}
```

### Invoke Agent

```
POST /api/v1/agents/{agent_name}/invoke
```

**Request Body:**
```json
{
  "message": "What is 5 + 5?",
  "session_id": "optional-session-id-for-conversation-continuity",
  "context": {}
}
```

**Response:**
```json
{
  "response": "5 + 5 equals 10.",
  "session_id": "generated-or-provided-session-id",
  "agent_name": "math_helper",
  "metadata": {}
}
```

### List Agents

```
GET /api/v1/agents
```

### Get Agent

```
GET /api/v1/agents/{agent_name}
```

### Delete Agent

```
DELETE /api/v1/agents/{agent_name}
```

---

## Best Practices

1. **Clear Tool Descriptions**: The LLM uses descriptions to decide when to call tools - be specific
2. **Handle Errors**: Your function code should handle errors gracefully
3. **Keep Functions Simple**: Complex logic should be broken into multiple tools
4. **Test Incrementally**: Start with a simple agent, then add tools one at a time
5. **Use Sessions**: Pass `session_id` to maintain conversation context across calls

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Agent not found" | Agent names can't have hyphens - use underscores |
| Empty response | Check system prompt guides the agent to use tools |
| Tool not called | Make tool description clear about when to use it |
| Function error | Check function code is valid Python with correct indentation |

---

## Links

- **API Docs**: https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/docs
- **Health Check**: https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/api/v1/health
