# Building Agents and Tools

This guide explains how to create agents, define tools, and how agents use tools in the A2A Self-Service platform.

## Table of Contents

- [Creating an Agent](#creating-an-agent)
- [Defining Tools](#defining-tools)
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

```bash
curl -X POST https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "definition": {
      "name": "calculator_agent",
      "display_name": "Calculator Agent",
      "description": "An agent that can perform calculations",
      "system_prompt": "You are a math assistant. When users ask for calculations, use the calculate tool to compute the result.",
      "tools": [
        {
          "name": "calculate",
          "description": "Evaluates a mathematical expression and returns the result",
          "parameters": {
            "type": "object",
            "properties": {
              "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')"
              }
            },
            "required": ["expression"]
          },
          "function_code": "def calculate(expression: str) -> str:\n    try:\n        result = eval(expression)\n        return f\"The result of {expression} is {result}\"\n    except Exception as e:\n        return f\"Error: {str(e)}\""
        }
      ]
    },
    "deploy_immediately": true
  }'
```

---

## Defining Tools

Tools are functions that agents can call to perform specific actions. Each tool has:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique tool name (valid Python identifier) |
| `description` | string | Yes | What the tool does - the LLM uses this to decide when to call it |
| `parameters` | object | No | JSON Schema defining the tool's input parameters |
| `function_code` | string | No | Python code implementing the tool function |

### Tool Parameters (JSON Schema)

Parameters follow JSON Schema format:

```json
{
  "type": "object",
  "properties": {
    "param_name": {
      "type": "string|number|boolean|array|object",
      "description": "What this parameter is for"
    }
  },
  "required": ["param_name"]
}
```

### Function Code Format

The `function_code` is a Python function definition as a string:

```python
def tool_name(param1: str, param2: int) -> str:
    # Your logic here
    return "result"
```

**Important:**
- The function name must match the tool `name`
- Use type hints for parameters
- Return a string (the result shown to the user)
- Keep functions self-contained (no external imports that aren't available)

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

```json
{
  "definition": {
    "name": "weather_agent",
    "display_name": "Weather Agent",
    "description": "An agent that provides weather information",
    "system_prompt": "You are a weather assistant. Use the get_weather tool when users ask about weather conditions in a city.",
    "tools": [
      {
        "name": "get_weather",
        "description": "Gets the current weather for a city",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {
              "type": "string",
              "description": "The city name (e.g., 'New York', 'London')"
            }
          },
          "required": ["city"]
        },
        "function_code": "def get_weather(city: str) -> str:\n    weather_data = {\n        'new york': 'Sunny, 72°F',\n        'london': 'Cloudy, 55°F',\n        'tokyo': 'Rainy, 65°F'\n    }\n    city_lower = city.lower()\n    if city_lower in weather_data:\n        return f\"Weather in {city}: {weather_data[city_lower]}\"\n    return f\"Weather data not available for {city}\""
      }
    ]
  },
  "deploy_immediately": true
}
```

### 2. Multi-Tool Agent

```json
{
  "definition": {
    "name": "utility_agent",
    "display_name": "Utility Agent",
    "description": "An agent with multiple utility tools",
    "system_prompt": "You are a utility assistant. Use the appropriate tool based on the user's request:\n- Use 'calculate' for math\n- Use 'convert_units' for unit conversions",
    "tools": [
      {
        "name": "calculate",
        "description": "Evaluates mathematical expressions",
        "parameters": {
          "type": "object",
          "properties": {
            "expression": {"type": "string", "description": "Math expression"}
          },
          "required": ["expression"]
        },
        "function_code": "def calculate(expression: str) -> str:\n    return f\"Result: {eval(expression)}\""
      },
      {
        "name": "convert_units",
        "description": "Converts between units (km to miles, celsius to fahrenheit, etc.)",
        "parameters": {
          "type": "object",
          "properties": {
            "value": {"type": "number", "description": "The value to convert"},
            "from_unit": {"type": "string", "description": "Source unit"},
            "to_unit": {"type": "string", "description": "Target unit"}
          },
          "required": ["value", "from_unit", "to_unit"]
        },
        "function_code": "def convert_units(value: float, from_unit: str, to_unit: str) -> str:\n    conversions = {\n        ('km', 'miles'): lambda x: x * 0.621371,\n        ('miles', 'km'): lambda x: x * 1.60934,\n        ('celsius', 'fahrenheit'): lambda x: x * 9/5 + 32,\n        ('fahrenheit', 'celsius'): lambda x: (x - 32) * 5/9\n    }\n    key = (from_unit.lower(), to_unit.lower())\n    if key in conversions:\n        result = conversions[key](value)\n        return f\"{value} {from_unit} = {result:.2f} {to_unit}\"\n    return f\"Conversion from {from_unit} to {to_unit} not supported\""
      }
    ]
  },
  "deploy_immediately": true
}
```

---

## API Reference

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
    "model": "string (optional, default: azure/gpt-4o)",
    "tools": [
      {
        "name": "string (required)",
        "description": "string (required)",
        "parameters": { "JSON Schema (optional)" },
        "function_code": "string (optional)"
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
