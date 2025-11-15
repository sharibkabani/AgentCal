.PHONY: help build up down restart logs shell clean setup

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup - copy env template
	@if [ ! -f .env ]; then \
		echo "Creating .env file from template..."; \
		cp env.template .env; \
		echo "✓ .env file created. Please edit it with your Google OAuth credentials."; \
	else \
		echo "✗ .env file already exists. Skipping."; \
	fi

build: ## Build the Docker image
	docker-compose build

up: ## Start the MCP server
	docker-compose up -d
	@echo "MCP server starting..."
	@echo "Check logs with: make logs"
	@echo "Health check: curl http://localhost:8001/health"

down: ## Stop the MCP server
	docker-compose down

restart: ## Restart the MCP server
	docker-compose restart

logs: ## Follow the server logs
	docker-compose logs -f mcp-server

shell: ## Open a shell in the running container
	docker-compose exec mcp-server /bin/bash

clean: ## Stop and remove containers, volumes, and images
	docker-compose down -v
	docker-compose rm -f

health: ## Check server health
	@curl -s http://localhost:8001/health | python -m json.tool || echo "Server not responding"

offerings: ## List available MCP offerings
	@curl -s http://localhost:8001/services/offerings | python -m json.tool || echo "Server not responding"

dev: ## Run in development mode with hot reload
	@echo "Starting in development mode..."
	docker-compose up

rebuild: ## Rebuild and restart
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "Server rebuilt and restarted"

