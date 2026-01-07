"""A2A tools for agent-to-agent communication."""

import httpx

from .registry import register_tool


@register_tool()
def call_agent(agent_name: str, message: str) -> str:
    """Call another agent and get its response.
    
    This enables agent-to-agent communication within the platform.
    
    Args:
        agent_name: The name of the agent to call (e.g., "weather_agent")
        message: The message to send to the agent
    
    Returns:
        The response from the called agent.
    """
    base_url = "https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{base_url}/a2a/agents/{agent_name}/tasks",
                json={
                    "message": {
                        "role": "user",
                        "parts": [{"type": "text", "text": message}]
                    }
                }
            )
            
            if response.status_code == 404:
                return f"Agent '{agent_name}' not found. Use list_agents to see available agents."
            
            response.raise_for_status()
            task = response.json()
            
            # Extract agent response from task messages
            for msg in reversed(task.get("messages", [])):
                if msg.get("role") == "agent":
                    for part in msg.get("parts", []):
                        if part.get("text"):
                            return part["text"]
            
            return "Agent did not provide a response."
            
    except httpx.TimeoutException:
        return f"Timeout calling agent '{agent_name}'. The agent may be processing a complex request."
    except Exception as e:
        return f"Error calling agent '{agent_name}': {str(e)}"


@register_tool()
def list_agents() -> str:
    """List all available agents that can be called.
    
    Returns:
        A list of available agent names and descriptions.
    """
    base_url = "https://a2a-selfservice-staging.victorioussea-2cc9367e.eastus.azurecontainerapps.io"
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{base_url}/api/v1/agents")
            response.raise_for_status()
            data = response.json()
            
            agents = data.get("agents", [])
            if not agents:
                return "No agents available."
            
            lines = ["Available agents:"]
            for agent in agents:
                name = agent.get("name", "unknown")
                desc = agent.get("description", "No description")
                status = agent.get("status", "unknown")
                lines.append(f"- {name}: {desc} (status: {status})")
            
            return "\n".join(lines)
            
    except Exception as e:
        return f"Error listing agents: {str(e)}"
