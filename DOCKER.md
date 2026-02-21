# Docker Deployment Guide

This guide explains how to run Local Daemon and its microservices using Docker for improved security, isolation, and deployment simplicity.

## Architecture

The dockerized setup consists of three components:

1. **Scraper Service** (`services/scraper/`) - Web scraping with Playwright
2. **Search Service** (`services/search/`) - Web search via Tavily API
3. **Agent** (main application) - LLM agent framework

All services communicate over a private Docker network (`agent-network`) and log to `./logs/` on the host.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- `.env` file configured (copy from `.env.example`)

## Quick Start

### 1. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env and set required values:
# - AGENT_LLM_MODEL (e.g., openai/gpt-4o)
# - OPENAI_API_KEY or ANTHROPIC_API_KEY
# - TAVILY_API_KEY (get from https://tavily.com)
```

### 2. Start Microservices

```bash
# Start scraper and search services
docker compose up -d

# Verify services are running
docker compose ps

# Check service health
curl http://localhost:8000/health  # Scraper
curl http://localhost:8001/health  # Search
```

### 3. Run the Agent

```bash
# Run agent with a task (automatically starts services if needed)
./run-agent.sh "What is the weather in San Francisco?"

# Skip the UNDERSTAND phase
./run-agent.sh --no-understand "List files in the current directory"
```

## Detailed Usage

### Managing Microservices

```bash
# Start services in foreground (see logs)
docker compose up

# Start services in background
docker compose up -d

# Stop services
docker compose down

# Restart a specific service
docker compose restart scraper
docker compose restart search

# View logs
docker compose logs -f scraper
docker compose logs -f search
docker compose logs --tail=100

# Rebuild after code changes
docker compose build
docker compose up -d
```

### Running the Agent

The `run-agent.sh` script handles:
- Starting microservices if not already running
- Building the agent Docker image
- Running the agent in an isolated container
- Logging output to `./logs/agent_TIMESTAMP.log`

```bash
# Basic usage
./run-agent.sh "Your task here"

# Skip UNDERSTAND phase for direct execution
./run-agent.sh --no-understand "Your task here"

# Examples
./run-agent.sh "Search for recent AI research papers"
./run-agent.sh "Scrape https://example.com and summarize the content"
./run-agent.sh --no-understand "What is 2 + 2?"
```

### Manual Agent Execution

If you prefer to run the agent manually:

```bash
# Build agent image
docker build -t local-daemon-agent:latest -f Dockerfile .

# Run agent
docker run --rm \
  --network local-daemon_agent-network \
  --env-file .env \
  -e HOST_GET_URL=http://scraper:8000 \
  -e HOST_WEB_SEARCH=http://search:8001 \
  -v "$(pwd)/logs:/app/logs" \
  local-daemon-agent:latest "Your task here"
```

## Configuration

### Environment Variables

All configuration is read from `.env`. Key variables:

#### LLM Configuration
```bash
AGENT_LLM_MODEL=openai/gpt-4o
OPENAI_API_KEY=sk-your-key-here
MAX_TOKENS=4096
```

#### Scraper Service
```bash
SCRAPER_PORT=8000                      # Host port
SCRAPER_FETCH_TIMEOUT_MS=15000         # Navigation timeout
SCRAPER_NETWORK_IDLE_TIMEOUT_MS=5000   # Network idle timeout
SCRAPER_ENABLE_LAZY_LOAD=true          # Scroll to load content
SCRAPER_MAX_SCROLL_ATTEMPTS=3          # Max scroll iterations
```

#### Search Service
```bash
SEARCH_PORT=8001                       # Host port
TAVILY_API_KEY=tvly-your-key-here      # Required
TAVILY_SEARCH_DEPTH=advanced           # basic or advanced
TAVILY_MIN_SCORE=0.0                   # Minimum result score
```

### Port Configuration

By default:
- Scraper: `http://localhost:8000`
- Search: `http://localhost:8001`

To change ports, edit `.env`:
```bash
SCRAPER_PORT=9000
SEARCH_PORT=9001
HOST_GET_URL=http://127.0.0.1:9000
HOST_WEB_SEARCH=http://127.0.0.1:9001
```

Then restart services:
```bash
docker compose down
docker compose up -d
```

## Logs

All services log to `./logs/`:

```bash
# Agent logs (timestamped)
logs/agent_20260221_153045.log

# View recent agent logs
ls -lt logs/agent_*.log | head -5

# Follow agent logs in real-time
tail -f logs/agent_*.log
```

Service logs are also available via Docker:
```bash
docker compose logs -f
```

## Troubleshooting

### Services Won't Start

**Check Docker daemon:**
```bash
docker ps
```

**Check .env file:**
```bash
cat .env | grep -E "TAVILY_API_KEY|AGENT_LLM_MODEL"
```

**View service logs:**
```bash
docker compose logs scraper
docker compose logs search
```

### "TAVILY_API_KEY not set" Error

The search service validates the API key on startup. If missing:

1. Get a key from https://tavily.com
2. Add to `.env`: `TAVILY_API_KEY=tvly-your-key-here`
3. Restart: `docker compose restart search`

### Agent Can't Connect to Services

**Verify services are running:**
```bash
docker compose ps
```

**Check network connectivity:**
```bash
docker network ls | grep agent-network
docker network inspect local-daemon_agent-network
```

**Test from host:**
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### Playwright Installation Issues (Scraper)

The scraper requires Playwright browsers. If the build fails:

```bash
# Rebuild with verbose output
docker compose build --no-cache scraper

# Check container logs
docker compose logs scraper
```

### Port Already in Use

If ports 8000 or 8001 are occupied:

```bash
# Find process using port
lsof -i :8000
lsof -i :8001

# Option 1: Stop conflicting process
kill <PID>

# Option 2: Change ports in .env
SCRAPER_PORT=9000
SEARCH_PORT=9001
```

### No Console Colors

Console colors should work automatically. If you don't see colors:

**Cause**: TTY not allocated or FORCE_COLOR not set
**Solution**: Colors are enabled by default via:
- `-t` flag allocates pseudo-TTY
- `FORCE_COLOR=1` environment variable
- `TERM=xterm-256color` for proper color support

These are already configured in `run-agent.sh`. If colors still don't work:

```bash
# Test manually
docker run --rm -t \
    -e FORCE_COLOR=1 \
    -e TERM=xterm-256color \
    local-daemon-agent:latest "test"

# Check your terminal supports colors
echo $TERM
tput colors  # Should show 256
```

**Note**: Log files (`logs/agent_*.log`) contain ANSI color codes. To view with colors:
```bash
# View with colors preserved
less -R logs/agent_*.log

# Or strip colors for plain text
cat logs/agent_*.log | sed 's/\x1b\[[0-9;]*m//g'
```

## Security Features

### Container Isolation

- Each service runs in its own container
- No direct access to host filesystem (except `./logs/`)
- Private network for inter-service communication
- Non-root user within containers (future enhancement)

### Network Security

- Services communicate over isolated bridge network
- Only specified ports exposed to host
- Agent container auto-removes after execution (`--rm`)

### Configuration Security

- `.env` file never copied into images (`.dockerignore`)
- Environment variables passed at runtime only
- API keys remain on host filesystem

## Performance

### Resource Limits

Add resource constraints in `docker-compose.yml`:

```yaml
services:
  scraper:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          memory: 512M
```

### Build Caching

Docker caches layers for faster rebuilds:

```bash
# Clean rebuild (no cache)
docker compose build --no-cache

# Normal rebuild (use cache)
docker compose build
```

### Volume Performance

For better I/O performance on macOS/Windows, consider named volumes:

```yaml
volumes:
  agent-logs:
    driver: local

services:
  scraper:
    volumes:
      - agent-logs:/app/logs
```

## Production Deployment

### Health Checks

Services include health checks:

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
```

Monitor health:
```bash
docker compose ps
```

### Restart Policies

Services auto-restart unless stopped:

```yaml
restart: unless-stopped
```

### Logging

Configure log rotation in `docker-compose.yml`:

```yaml
services:
  scraper:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Development Workflow

### Code Changes

After modifying code:

```bash
# Rebuild affected service
docker compose build scraper  # or search
docker compose up -d

# Rebuild agent
docker build -t local-daemon-agent:latest -f Dockerfile .
```

### Live Reload

Enable auto-reload for development:

```bash
# In .env
SCRAPER_RELOAD=true
SEARCH_RELOAD=true
```

Then mount code as volumes in `docker-compose.yml`:

```yaml
services:
  scraper:
    volumes:
      - ./services/scraper/scraper.py:/app/scraper.py
```

### Testing

Run tests in containers:

```bash
# Unit tests
docker run --rm \
  -v "$(pwd):/app" \
  local-daemon-agent:latest \
  python -m pytest tests/

# Integration tests (with services)
docker compose up -d
docker run --rm \
  --network local-daemon_agent-network \
  -v "$(pwd):/app" \
  local-daemon-agent:latest \
  python -m pytest tests/integration/
```

## Cleanup

### Remove Containers and Networks

```bash
# Stop and remove containers
docker compose down

# Remove containers, networks, and volumes
docker compose down -v

# Remove images as well
docker compose down --rmi all
```

### Clean Logs

```bash
# Remove old agent logs (keep last 10)
ls -t logs/agent_*.log | tail -n +11 | xargs rm -f

# Clean all logs
rm -f logs/agent_*.log
```

## Comparison: Docker vs. Native

| Feature | Docker | Native (venv) |
|---------|--------|---------------|
| Isolation | ✅ Full | ❌ Partial |
| Security | ✅ Sandboxed | ⚠️ Host-level |
| Deployment | ✅ Portable | ⚠️ Environment-dependent |
| Performance | ⚠️ Slight overhead | ✅ Native |
| Setup complexity | ⚠️ Docker required | ✅ Python only |
| Resource usage | ⚠️ Higher (containers) | ✅ Lower |

**Recommendation**: Use Docker for production/deployment, native for development.

## Next Steps

- **Production**: Configure reverse proxy (nginx) and HTTPS
- **Monitoring**: Integrate with Prometheus/Grafana
- **Scaling**: Use Docker Swarm or Kubernetes
- **CI/CD**: Automate builds with GitHub Actions

## Support

For issues or questions:
1. Check logs: `docker compose logs`
2. Verify configuration: `cat .env`
3. Test services manually: `curl http://localhost:8000/health`
4. Review this documentation
5. Check project CLAUDE.md for architecture details
