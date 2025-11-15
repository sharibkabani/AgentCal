.PHONY: help build up down restart logs shell clean setup

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Setup credentials (run npm run setup)
	@echo "Running Google OAuth setup..."
	npm run setup
	@echo "✓ Setup complete. Credentials saved."

build: ## Build the Docker image
	docker-compose build

up: ## Start the Google Meet MCP server
	docker-compose up -d
	@echo "Google Meet MCP server starting..."
	@echo "Check logs with: make logs"

down: ## Stop the Google Meet MCP server
	docker-compose down

restart: ## Restart the server
	docker-compose restart

logs: ## Follow the server logs
	docker-compose logs -f google-meet-mcp

shell: ## Open a shell in the running container
	docker-compose exec google-meet-mcp /bin/sh

clean: ## Stop and remove containers and volumes
	docker-compose down -v

rebuild: ## Rebuild and restart
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "Google Meet MCP server rebuilt and restarted"

