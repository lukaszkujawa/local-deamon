#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first:"
    log_error "  https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    log_error "Docker Compose is not installed or too old."
    log_error "Please install Docker Compose 2.0+:"
    log_error "  https://docs.docker.com/compose/install/"
    exit 1
fi

if [ ! -f .env ]; then
    log_warn ".env file not found. Creating from .env.example..."
    cp .env.example .env
    log_warn "Please edit .env and configure:"
    log_warn "  - AGENT_LLM_MODEL"
    log_warn "  - OPENAI_API_KEY or ANTHROPIC_API_KEY"
    log_warn "  - TAVILY_API_KEY"
    log_error "Exiting. Configure .env and run this script again."
    exit 1
fi

if ! grep -q "TAVILY_API_KEY=tvly-" .env && ! grep -q "^TAVILY_API_KEY=.\{20,\}" .env; then
    log_error "TAVILY_API_KEY not configured in .env"
    log_error "Get an API key from https://tavily.com and add it to .env"
    exit 1
fi

mkdir -p logs

if docker compose ps | grep -q "local-daemon-scraper\|local-daemon-search"; then
    log_warn "Services are already running. Stopping them first..."
    docker compose down
    log_info "Services stopped. Starting fresh..."
fi

log_info "Building Docker images..."
docker compose build

if ! docker image inspect local-daemon-agent:latest > /dev/null 2>&1; then
    log_info "Building agent image..."
    docker build -t local-daemon-agent:latest -f Dockerfile .
else
    log_info "Agent image already exists (use 'make build' to rebuild)"
fi

log_info "Starting microservices..."
docker compose up -d

log_info "Waiting for services to be healthy..."
sleep 3

MAX_WAIT=30
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -sf http://localhost:8000/health > /dev/null && \
       curl -sf http://localhost:8001/health > /dev/null; then
        log_info "All services are healthy!"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    log_warn "Services took longer than expected to start. Check status:"
    docker compose ps
    log_warn "View logs with: docker compose logs"
else
    log_info "Services are ready!"
    echo ""
    log_info "Scraper: http://localhost:8000/health"
    log_info "Search:  http://localhost:8001/health"
    echo ""
    log_info "Run the agent with: ./run-agent.sh \"Your task here\""
    log_info "View logs with: docker compose logs -f"
    log_info "Stop services with: docker compose down"
fi
