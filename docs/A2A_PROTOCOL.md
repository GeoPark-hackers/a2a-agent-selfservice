# A2A (Agent-to-Agent) Protocol

This guide explains how to use the A2A protocol to enable agent discovery and inter-agent communication.

## Table of Contents

- [Overview](#overview)
- [Agent Discovery](#agent-discovery)
- [Task API](#task-api)
- [Agent-to-Agent Communication](#agent-to-agent-communication)
- [API Reference](#api-reference)

---

## Overview

A2A is a protocol that enables agents to:

1. **Discover** each other's capabilities
2. **Communicate** through a standardized task-based API
3. **Orchestrate** complex workflows by delegating to specialized agents

```
┌─────────────────┐         A2A Task         ┌─────────────────┐
│  Orchestrator   │ ───────────────────────▶ │ Utility Agent   │
│     Agent       │                          │                 │
│                 │ ◀─────────────────────── │                 │
└─────────────────┘       Task Response      └─────────────────┘
```

---

## Agent Discovery

### Platform Discovery

Get information about the platform:

```bash
curl https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/.well-known/agent.json
```

Response:
```json
{
  "name": "A2A Self-Service Platform",
  "description": "Platform for creating and managing AI agents",
  "url": "https://a2a-selfservice-staging...",
  "version": "0.1.0",
  "protocol_version": "0.1",
  "agents_endpoint": "/api/v1/agents",
  "a2a_base": "/a2a"
}
```

### Agent Card

Get a specific agent's capabilities (skills/tools):

```bash
curl https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/a2a/agents/utility_assistant/agent.json
```

Response:
```json
{
  "name": "utility_assistant",
  "description": "Assistant with calculator, weather, and utility tools",
  "url": "https://.../a2a/agents/utility_assistant",
  "version": "1.0.0",
  "skills": [
    {
      "id": "calculate",
      "name": "calculate",
      "description": "Evaluate math expressions",
      "parameters": []
    },
    {
      "id": "get_weather",
      "name": "get_weather",
      "description": "Get weather for a city",
      "parameters": []
    }
  ],
  "protocol_version": "0.1",
  "provider": {
    "name": "A2A Self-Service Platform",
    "url": "https://..."
  }
}
```

---

## Task API

Tasks represent a unit of work with an agent. Each task maintains conversation state.

### Create a Task

Start a new conversation with an agent:

```bash
curl -X POST https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/a2a/agents/utility_assistant/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "parts": [{"type": "text", "text": "What is 25 * 4?"}]
    }
  }'
```

Response:
```json
{
  "id": "7df2353f-fd84-49b2-8571-68c255f5b485",
  "session_id": "4bbc532b-e5f3-47b1-afc8-d185772e2ca4",
  "state": "completed",
  "messages": [
    {
      "role": "user",
      "parts": [{"type": "text", "text": "What is 25 * 4?"}]
    },
    {
      "role": "agent",
      "parts": [{"type": "text", "text": "The result of 25 × 4 is 100."}]
    }
  ],
  "artifacts": [],
  "created_at": "2026-01-07T03:59:43.691480"
}
```

### Get Task Status

Check the status of an existing task:

```bash
curl https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/a2a/agents/utility_assistant/tasks/{task_id}
```

### Continue Conversation

Send a follow-up message to an existing task:

```bash
curl -X POST https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/a2a/agents/utility_assistant/tasks/{task_id}/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "parts": [{"type": "text", "text": "Now divide that by 2"}]
    }
  }'
```

### Cancel Task

Cancel an in-progress task:

```bash
curl -X POST https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/a2a/agents/utility_assistant/tasks/{task_id}/cancel
```

### Task States

| State | Description |
|-------|-------------|
| `submitted` | Task created, waiting to be processed |
| `working` | Agent is processing the task |
| `input-required` | Agent needs more input from user |
| `completed` | Task finished successfully |
| `canceled` | Task was canceled |
| `failed` | Task failed with an error |

---

## Agent-to-Agent Communication

Agents can call other agents using the `call_agent` tool.

### Create an Orchestrator Agent

```bash
curl -X POST https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "definition": {
      "name": "orchestrator",
      "display_name": "Orchestrator Agent",
      "description": "An agent that can delegate tasks to other agents",
      "system_prompt": "You are an orchestrator. Use call_agent to delegate tasks to specialized agents. Use list_agents to see available agents.",
      "tools": [
        {"name": "call_agent", "description": "Call another agent"},
        {"name": "list_agents", "description": "List available agents"}
      ]
    },
    "deploy_immediately": true
  }'
```

### Delegate a Task

```bash
curl -X POST https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/api/v1/agents/orchestrator/invoke \
  -H "Content-Type: application/json" \
  -d '{"message": "Ask utility_assistant what the weather is in Tokyo"}'
```

Response:
```json
{
  "response": "The weather in Tokyo is rainy with a temperature of 65°F and humidity of 82%.",
  "session_id": "...",
  "agent_name": "orchestrator"
}
```

### How It Works

```
1. User → Orchestrator: "Ask utility_assistant about weather in Tokyo"
2. Orchestrator uses call_agent tool → utility_assistant
3. utility_assistant processes request, uses get_weather tool
4. utility_assistant → Orchestrator: "65°F, Rainy, 82% humidity"
5. Orchestrator → User: "The weather in Tokyo is rainy, 65°F..."
```

### A2A Tools

| Tool | Description |
|------|-------------|
| `call_agent` | Call another agent by name with a message |
| `list_agents` | List all available agents and their descriptions |

---

## API Reference

### Discovery Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/.well-known/agent.json` | Platform discovery |
| GET | `/a2a/agents/{name}/agent.json` | Agent card (capabilities) |

### Task Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/a2a/agents/{name}/tasks` | Create new task |
| GET | `/a2a/agents/{name}/tasks/{id}` | Get task status |
| POST | `/a2a/agents/{name}/tasks/{id}/messages` | Send message to task |
| POST | `/a2a/agents/{name}/tasks/{id}/cancel` | Cancel task |

### Message Format

```json
{
  "message": {
    "role": "user",
    "parts": [
      {
        "type": "text",
        "text": "Your message here"
      }
    ]
  },
  "session_id": "optional-session-id",
  "metadata": {}
}
```

### Task Response Format

```json
{
  "id": "task-uuid",
  "session_id": "session-uuid",
  "state": "completed|working|failed|...",
  "messages": [
    {"role": "user", "parts": [...]},
    {"role": "agent", "parts": [...]}
  ],
  "artifacts": [],
  "metadata": {},
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp"
}
```

---

## Examples

### Multi-Agent Workflow

Create specialized agents:

```bash
# Weather specialist
curl -X POST .../api/v1/agents -d '{
  "definition": {
    "name": "weather_specialist",
    "system_prompt": "You provide weather information.",
    "tools": [{"name": "get_weather"}, {"name": "get_forecast"}]
  },
  "deploy_immediately": true
}'

# Math specialist  
curl -X POST .../api/v1/agents -d '{
  "definition": {
    "name": "math_specialist",
    "system_prompt": "You solve math problems.",
    "tools": [{"name": "calculate"}, {"name": "convert_units"}]
  },
  "deploy_immediately": true
}'

# Orchestrator that uses both
curl -X POST .../api/v1/agents -d '{
  "definition": {
    "name": "smart_assistant",
    "system_prompt": "Route weather questions to weather_specialist and math to math_specialist.",
    "tools": [{"name": "call_agent"}, {"name": "list_agents"}]
  },
  "deploy_immediately": true
}'
```

Then use the orchestrator:

```bash
curl -X POST .../api/v1/agents/smart_assistant/invoke \
  -d '{"message": "What is the weather in Paris and what is 100 km in miles?"}'
```

---

## Links

- **API Docs**: https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/docs
- **Agents & Tools Guide**: [AGENTS_AND_TOOLS.md](./AGENTS_AND_TOOLS.md)
- **Platform Discovery**: https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io/.well-known/agent.json
