.PHONY: help start stop restart logs build clean run test health

help:
	@echo "Local Daemon - Docker Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make start        - Start all microservices"
	@echo "  make build        - Build all Docker images"
	@echo "  make stop         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs         - Follow service logs"
	@echo "  make health       - Check service health"
	@echo "  make ps           - Show running containers"
	@echo ""
	@echo "Development:"
	@echo "  make rebuild      - Rebuild and restart services"
	@echo "  make clean        - Remove containers, networks, and volumes"
	@echo "  make clean-logs   - Remove old log files"
	@echo ""
	@echo "Running:"
	@echo "  make run TASK=\"Your task here\"  - Run agent with task"
	@echo ""
	@echo "Examples:"
	@echo "  make start"
	@echo "  make run TASK=\"What is the weather?\""
	@echo "  make logs"

start:
	@echo "Starting microservices..."
	@./docker-start.sh

stop:
	@echo "Stopping services..."
	@docker compose down

restart: stop start

logs:
	@docker compose logs -f

build:
	@echo "Building Docker images..."
	@docker compose build
	@docker build -t local-daemon-agent:latest -f Dockerfile .
	@echo ""
	@echo "Images built successfully!"
	@echo "Note: Agent code is mounted as volumes - no rebuild needed for code changes."
	@echo "Only rebuild when dependencies (requirements.txt) change."

rebuild: build restart

rebuild-agent:
	@echo "Rebuilding agent image only..."
	@docker build -t local-daemon-agent:latest -f Dockerfile .

ps:
	@docker compose ps

health:
	@echo "Checking service health..."
	@echo -n "Scraper: "
	@curl -sf http://localhost:8000/health && echo "✓ Healthy" || echo "✗ Unhealthy"
	@echo -n "Search:  "
	@curl -sf http://localhost:8001/health && echo "✓ Healthy" || echo "✗ Unhealthy"

run:
ifndef TASK
	@echo "Usage: make run TASK=\"Your task here\""
	@exit 1
endif
	@./run-agent.sh "$(TASK)"

clean:
	@echo "Removing containers, networks, and volumes..."
	@docker compose down -v
	@docker rmi local-daemon-agent:latest 2>/dev/null || true

clean-logs:
	@echo "Removing old log files (keeping last 10)..."
	@ls -t logs/agent_*.log 2>/dev/null | tail -n +11 | xargs rm -f
	@echo "Done"

test:
	@echo "Testing services..."
	@make health
