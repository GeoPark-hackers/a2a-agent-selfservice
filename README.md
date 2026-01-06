# A2A Agent Self-Service Platform

A self-service platform for creating and managing AI agents using **Google ADK (Agent Development Kit)** with **A2A (Agent-to-Agent) protocol**, deployed on **Azure Container Apps**.

## Overview

This platform enables teams to:
- **Create agents dynamically** via a REST API
- **Expose agents via A2A protocol** for inter-agent communication
- **Deploy to Azure** with CI/CD pipelines
- **Use Azure OpenAI or Google AI** as LLM providers

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Container Apps                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │            A2A Self-Service API (FastAPI)           │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │   Agent 1   │  │   Agent 2   │  │   Agent N   │  │    │
│  │  │   (ADK)     │  │   (ADK)     │  │   (ADK)     │  │    │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │    │
│  │         │                │                │         │    │
│  │         └────────────────┼────────────────┘         │    │
│  │                    A2A Protocol                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                              │                               │
│              ┌───────────────┼───────────────┐               │
│              ▼               ▼               ▼               │
│       Azure OpenAI    Azure Key Vault    Redis Cache         │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker
- Azure CLI (for deployment)
- GitHub CLI (for repository operations)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/GeoPark-hackers/a2a-agent-selfservice.git
   cd a2a-agent-selfservice
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   python -m a2a_selfservice.main
   ```

5. **Access the API**
   - Swagger UI: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/v1/health

### Docker

```bash
docker build -t a2a-agent-selfservice .
docker run -p 8000:8000 --env-file .env a2a-agent-selfservice
```

## Documentation

📚 **[Building Agents and Tools Guide](docs/AGENTS_AND_TOOLS.md)** - Complete guide on creating agents, defining tools, and how agents use tools.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/agents` | Create a new agent |
| GET | `/api/v1/agents` | List all agents |
| GET | `/api/v1/agents/{name}` | Get agent details |
| POST | `/api/v1/agents/{name}/deploy` | Deploy an agent |
| DELETE | `/api/v1/agents/{name}` | Delete an agent |
| POST | `/api/v1/agents/{name}/invoke` | Invoke an agent |

### Create an Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "definition": {
      "name": "customer_support_agent",
      "display_name": "Customer Support Agent",
      "description": "Handles customer inquiries",
      "system_prompt": "You are a helpful customer support agent...",
      "tools": []
    },
    "deploy_immediately": true
  }'
```

> **Note:** Agent names must be valid Python identifiers - use underscores, not hyphens.

### Invoke an Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/customer_support_agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How can I reset my password?",
    "session_id": "user-123-session"
  }'
```

## Azure Deployment

### Infrastructure Setup

1. **Create Azure resources using Bicep**
   ```bash
   az group create --name a2a-selfservice-rg --location eastus
   
   az deployment group create \
     --resource-group a2a-selfservice-rg \
     --template-file infra/main.bicep \
     --parameters environment=staging
   ```

2. **Configure GitHub Secrets**
   - `AZURE_CREDENTIALS`: Service principal credentials
   - `ACR_USERNAME`: Azure Container Registry username
   - `ACR_PASSWORD`: Azure Container Registry password

3. **Set GitHub Variables**
   - `AZURE_CONTAINER_REGISTRY`: ACR name
   - `AZURE_RESOURCE_GROUP`: Resource group name

### CI/CD Pipeline

The project includes two GitHub Actions workflows:

- **CI** (`ci.yml`): Runs on every PR and push
  - Linting with Ruff
  - Type checking with mypy
  - Unit tests with pytest
  - Docker build verification

- **Deploy** (`deploy-azure.yml`): Deploys to Azure
  - Builds and pushes Docker image to ACR
  - Deploys to staging automatically on `main` branch
  - Manual approval for production deployment

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (`azure_openai` or `google_ai`) | `azure_openai` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | - |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | - |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Model deployment name | `gpt-4o` |
| `GOOGLE_API_KEY` | Google AI API key | - |
| `APP_ENV` | Environment (`development`, `staging`, `production`) | `development` |
| `APP_PORT` | Application port | `8000` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |

## Why ADK for Azure?

**Google ADK is deployment-agnostic**, making it an excellent choice for Azure:

1. **Model Agnostic**: Works with Azure OpenAI, Google AI, or any OpenAI-compatible API
2. **Framework Agnostic**: Integrates with FastAPI, Flask, or any Python web framework
3. **A2A Protocol Support**: Built-in support for agent-to-agent communication
4. **Containerized Deployment**: Easy to package and deploy as Docker containers
5. **Extensible**: Rich tool and sub-agent support for complex workflows

## Project Structure

```
a2a-agent-selfservice/
├── src/a2a_selfservice/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration management
│   ├── models.py         # Pydantic models
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py     # API endpoints
│   └── agents/
│       ├── __init__.py
│       ├── base.py       # Agent factory
│       └── registry.py   # Agent registry
├── tests/
├── infra/
│   └── main.bicep        # Azure infrastructure
├── .github/workflows/
│   ├── ci.yml
│   └── deploy-azure.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

## License

MIT License - see [LICENSE](LICENSE) for details.
