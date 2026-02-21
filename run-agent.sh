#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source .env 2>/dev/null || true

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

if [ ! -f .env ]; then
    log_error ".env file not found! Please create one from .env.example"
    exit 1
fi

mkdir -p logs

if ! docker compose ps | grep -q "local-daemon-scraper"; then
    log_info "Starting microservices..."
    docker compose up -d
    log_info "Waiting for services to be healthy..."
    sleep 5
else
    log_info "Microservices already running"
fi

log_info "Checking service health..."
if ! docker compose ps | grep -q "local-daemon-scraper.*healthy\|Up"; then
    log_warn "Scraper service not healthy yet, waiting..."
    sleep 5
fi

if ! docker compose ps | grep -q "local-daemon-search.*healthy\|Up"; then
    log_warn "Search service not healthy yet, waiting..."
    sleep 5
fi

if [ $# -eq 0 ]; then
    log_error "Usage: ./run-agent.sh [--no-understand] \"Your task here\""
    log_error "Example: ./run-agent.sh \"What is the weather today?\""
    exit 1
fi

if ! docker image inspect local-daemon-agent:latest > /dev/null 2>&1; then
    log_info "Agent image not found. Building for the first time..."
    docker build -t local-daemon-agent:latest -f Dockerfile .
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/agent_${TIMESTAMP}.log"

log_info "Running agent (logs: $LOG_FILE)..."

docker run --rm -t \
    --network local-daemon_agent-network \
    --env-file .env \
    -e HOST_GET_URL=http://scraper:8000 \
    -e HOST_WEB_SEARCH=http://search:8001 \
    -e FORCE_COLOR=1 \
    -e TERM=xterm-256color \
    -v "${SCRIPT_DIR}/main.py:/app/main.py:ro" \
    -v "${SCRIPT_DIR}/localdeamon:/app/localdeamon:ro" \
    -v "${SCRIPT_DIR}/spellbook:/app/spellbook:ro" \
    -v "${SCRIPT_DIR}/tools:/app/tools:ro" \
    -v "${SCRIPT_DIR}/logs:/app/logs" \
    local-daemon-agent:latest "$@" 2>&1 | tee "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    log_info "Agent completed successfully"
else
    log_error "Agent failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
