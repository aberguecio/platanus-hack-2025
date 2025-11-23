# Start development environment with logs
dev:
	@echo "Starting development environment..."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo ""
	docker compose -f docker-compose.local.yml up

# View all service logs
logs:
	docker compose -f docker-compose.local.yml logs -f

# Create a new migration (usage: make migration MSG="your migration message")
migration:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG parameter is required. Usage: make migration MSG=\"your message\""; \
		exit 1; \
	fi
	@echo "Creating migration: $(MSG)..."
	docker compose -f docker-compose.local.yml exec backend alembic revision --autogenerate -m "$(MSG)"
	@echo "Migration created successfully!"

# Apply database migrations
migrate:
	@echo "Applying database migrations..."
	docker compose -f docker-compose.local.yml exec backend alembic upgrade head
	@echo "Migrations applied successfully!"

# Reset database completely
db-reset:
	@echo "Resetting database (this will delete all data)..."
	docker compose -f docker-compose.local.yml down -v
	docker compose -f docker-compose.local.yml up -d
	@echo "Database reset complete!"

# Complete fresh start (reset + rebuild)
fresh:
	@echo "Starting fresh (reset + rebuild)..."
	docker compose -f docker-compose.local.yml down -v
	docker compose -f docker-compose.local.yml up -d --build
	@echo ""
	@echo "Fresh environment ready!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000/docs"

# Show available commands
help:
	@echo "Available commands:"
	@echo "  make dev              - Start development environment with logs"
	@echo "  make logs             - View all service logs (after starting detached)"
	@echo "  make migration MSG=  - Create a new migration (e.g., make migration MSG=\"add user table\")"
	@echo "  make migrate          - Apply database migrations"
	@echo "  make db-reset         - Reset database (deletes all data)"
	@echo "  make fresh            - Complete reset + rebuild"
	@echo "  make help             - Show this help message"
