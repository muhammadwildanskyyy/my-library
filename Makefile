.PHONY: help install dev docker-up docker-down docker-build docker-logs \
       migrate migrate-create migrate-downgrade \
       lint format typecheck test clean

# =============================================================================
# AI Librarian Platform — Makefile
# =============================================================================

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Setup -------------------------------------------------------------------

install: ## Install dependencies with uv
	uv sync

install-dev: ## Install with dev dependencies
	uv sync --extra dev

# --- Docker ------------------------------------------------------------------

docker-up: ## Start all services (detached)
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

docker-build: ## Rebuild and start all services
	docker compose up -d --build

docker-logs: ## Tail logs from all services
	docker compose logs -f

docker-logs-app: ## Tail logs from app only
	docker compose logs -f app

docker-restart: ## Restart app service (keeps DB)
	docker compose restart app

# --- Database Migrations -----------------------------------------------------

migrate: ## Run all pending migrations
	uv run alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create msg="add users")
	uv run alembic revision --autogenerate -m "$(msg)"

migrate-downgrade: ## Downgrade one migration
	uv run alembic downgrade -1

migrate-docker: ## Run migrations inside Docker
	docker compose exec app alembic upgrade head

migrate-create-docker: ## Create migration inside Docker (usage: make migrate-create-docker msg="init")
	docker compose exec app alembic revision --autogenerate -m "$(msg)"

# --- Development -------------------------------------------------------------

dev: ## Run dev server locally (outside Docker)
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# --- Code Quality ------------------------------------------------------------

lint: ## Lint with ruff
	uv run ruff check app/ tests/

format: ## Format with ruff
	uv run ruff format app/ tests/

typecheck: ## Type check with mypy
	uv run mypy app/

test: ## Run tests
	uv run pytest -v

# --- Cleanup -----------------------------------------------------------------

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage
