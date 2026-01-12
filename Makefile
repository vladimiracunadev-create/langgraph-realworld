# LangGraph Real-World Cases - Developer shortcuts
# Usage: make lint | make test-case09 | make up | make down

.PHONY: help lint format test-case09 up down

help:
	@echo "Targets:"
	@echo "  make lint        - ruff check (Case 09 backend src)"
	@echo "  make format      - ruff format (Case 09 backend src)"
	@echo "  make test-case09 - pytest (Case 09 backend)"
	@echo "  make up          - docker compose up (site + case09)"
	@echo "  make down        - docker compose down"

lint:
	ruff check cases/09-rrhh-screening-agenda/backend/src

format:
	ruff format cases/09-rrhh-screening-agenda/backend/src

test-case09:
	pytest -q cases/09-rrhh-screening-agenda/backend/tests

up:
	docker compose up --build

down:
	docker compose down
