.PHONY: help lint test check build

help: ## Show available targets
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-8s %s\n", $$1, $$2}'

lint: ## Ruff lint and format check
	uv run ruff check .
	uv run ruff format --check .

test: ## Run pytest
	uv run pytest

check: lint test ## Lint + test

build: ## Generate .tex from JSON data
	uv run cv-build
