# LangGraph Real-World Cases - Developer shortcuts
# Usage: make lint | make test-case09 | make up | make down

.PHONY: help lint format test-case09 up down hub-list hub-run case-up case-down k8s-apply

help:
	@echo "Targets:"
	@echo "  make lint           - ruff check (Case 09 backend src)"
	@echo "  make format         - ruff format (Case 09 backend src)"
	@echo "  make test-case09    - pytest (Case 09 backend)"
	@echo "  make up             - docker compose up (site + case09)"
	@echo "  make down           - docker compose down"
	@echo "  make hub-list       - List all cases via Hub CLI"
	@echo "  make hub-run CASE=xx - Run a case via Hub CLI"
	@echo "  make case-up CASE=xx - Stand up a case via its compose"
	@echo "  make k8s-apply CASE=xx - Apply K8s manifests for a case"

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

hub-list:
	python hub.py list

hub-run:
	python hub.py run $(CASE)

hub-doctor:
	python hub.py doctor

case-up:
	@if [ -z "$(CASE)" ]; then echo "Error: CASE is required (e.g. make case-up CASE=09)"; exit 1; fi
	python hub.py serve $(CASE)

case-down:
	docker compose down

k8s-apply:
	@if [ -z "$(CASE)" ]; then echo "Error: CASE is required"; exit 1; fi
	kubectl apply -k k8s/cases/$(CASE)-*

