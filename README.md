# Local Daemon 👿

A tiny LLM sidekick that lives on your machine, runs your errands (read, write, exec, fetch, search), and keeps the chaos to a minimum.
Lightweight, useful, and only mildly mischievous.

## Quick Start

### Option 1: Docker (Recommended)

Docker is the preferred way to run the agent. Running it directly would otherwise give it full, unrestricted access to your filesystem and machine. 

```bash
# 1. Start microservices
./docker-start.sh

# 2. Run the agent
./run-agent.sh "What is the weather in San Francisco?"
```

See [DOCKER.md](DOCKER.md) for complete Docker documentation.

### Option 2: Native Python (Development)

Run at your own risk 👿

```bash
# 1. Install dependencies
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Start microservices (in separate terminals)
cd services/scraper && pip install -r requirements.txt && python scraper.py
cd services/search && pip install -r requirements.txt && python search.py

# 3. Run the agent
python main.py "What is the weather in San Francisco?"
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# LLM Provider
AGENT_LLM_MODEL=openai/gpt-4o
OPENAI_API_KEY=sk-your-key-here

# Microservices
HOST_GET_URL=http://127.0.0.1:8000
HOST_WEB_SEARCH=http://127.0.0.1:8001
TAVILY_API_KEY=tvly-your-key-here
```

## Architecture

### Core Components

- **Daemon** (`localdeamon/deamon.py`) - Main agentic loop orchestrator
- **LLM** (`localdeamon/llm.py`) - Provider-agnostic LLM abstraction
- **Tools** (`localdeamon/tools/`) - Extensible tool system
- **Context** (`localdeamon/context.py`) - Message history manager
- **Spells** (`localdeamon/spell.py`) - Type-safe function composition

### Microservices

- **Scraper** (`services/scraper/`) - Web scraping with Playwright
  - Stealth mode, lazy loading, configurable timeouts
  - Health check: `http://localhost:8000/health`

- **Search** (`services/search/`) - Web search via Tavily API
  - Quality filtering, multiple providers, configurable depth
  - Health check: `http://localhost:8001/health`

## Usage Examples

```bash
# Basic query
python main.py "What is 5 + 3?"

# Web search
python main.py "Find recent AI research papers"

# Web scraping
python main.py "Scrape https://example.com and summarize"

# File operations
python main.py "List all Python files and count their lines"

# Skip UNDERSTAND phase for direct execution
python main.py --no-understand "What is the capital of France?"
```

## Tools

Built-in tools (auto-registered):

- **exec**(command) - Execute shell commands (30s timeout)
- **read**(file_path) - Read files (10MB limit)
- **write**(file_path, content) - Write files with auto-directory creation
- **fetch**(url) - Scrape web pages via scraper microservice
- **search**(query) - Search the web via search microservice

See [CLAUDE.md](CLAUDE.md) for adding custom tools.

## Development

### Project Structure

```
local-daemon/
├── main.py                 # CLI entry point
├── localdeamon/            # Core framework
│   ├── deamon.py          # Agentic loop
│   ├── llm.py             # LLM providers
│   ├── tool_registry.py   # Tool system
│   ├── context.py         # Message history
│   └── tools/             # Built-in tools
├── services/              # Microservices
│   ├── scraper/          # Web scraping
│   └── search/           # Web search
├── spellbook/            # Prompt templates
└── docker-compose.yml    # Docker orchestration
```

### Adding a New Tool

```python
# localdeamon/tools/my_tool.py
from localdeamon.tool_registry import tool

@tool
def my_tool(param: str) -> str:
    """Description for LLM"""
    return result

# Register in tool_registry.py
def register_builtin(cls) -> None:
    from localdeamon.tools import exec, read, write, fetch, search, my_tool
```

## Docker Deployment

Complete Docker setup with:
- Isolated containers for each service
- Shared logging to `./logs/`
- Health checks and auto-restart
- Private network for inter-service communication

Commands:

```bash
./docker-start.sh           # Start services (auto-restarts if running)
./run-agent.sh "task"       # Run agent
docker compose restart      # Quick restart (no rebuild)
make restart                # Same as above
docker compose logs -f      # View logs
docker compose down         # Stop services
```

## Requirements

- Python 3.14+
- Docker 20.10+ (for containerized deployment)
- API Keys:
  - Ollama/OpenAI/Anthropic (for LLM)
  - Tavily (for web search)

