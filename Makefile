# LangGraph Real-World Cases - Developer shortcuts
# Usage: make lint | make test-case09 | make up | make down

.PHONY: help lint format test-case03 test-case09 test-case10 test-case13 test-case19 test-case25 compile-case13 up down hub-list hub-doctor hub-run case-up case-down k8s-apply pip-compile pip-compile-check

help:
	@echo "Targets:"
	@echo "  make lint              - ruff check (Case 09/10/13 backend src)"
	@echo "  make format            - ruff format (Case 09/10/13 backend src)"
	@echo "  make test-case03       - pytest (Case 03 backend)"
	@echo "  make test-case09       - pytest (Case 09 backend)"
	@echo "  make test-case10       - pytest (Case 10 backend)"
	@echo "  make test-case13       - pytest (Case 13 backend)"
	@echo "  make test-case19       - pytest (Case 19 backend)"
	@echo "  make test-case25       - pytest (Case 25 backend)"
	@echo "  make compile-case13    - syntax check (Case 13 backend src)"
	@echo "  make up                - docker compose up (todos los casos operativos)"
	@echo "  make down              - docker compose down"
	@echo "  make pip-compile       - regenerate requirements.txt lock files from requirements.in"
	@echo "  make pip-compile-check - check for drift between requirements.in and requirements.txt"
	@echo "  make hub-list          - List all cases via Hub CLI"
	@echo "  make hub-doctor        - Check Hub CLI environment"
	@echo "  make hub-run CASE=xx   - Run a case via Hub CLI"
	@echo "  make case-up CASE=xx   - Stand up a case via its compose"
	@echo "  make k8s-apply CASE=xx - Apply K8s manifests for a case"

pip-compile:
	bash scripts/pip-compile-all.sh

pip-compile-check:
	bash scripts/pip-compile-all.sh --check

lint:
	ruff check cases/09-rrhh-screening-agenda/backend/src cases/10-onboarding-empleados/backend/src cases/13-bi-analista-datos/backend/src

format:
	ruff format cases/09-rrhh-screening-agenda/backend/src cases/10-onboarding-empleados/backend/src cases/13-bi-analista-datos/backend/src

test-case03:
	pytest -q cases/03-incident-response-sre/backend/tests

test-case09:
	pytest -q cases/09-rrhh-screening-agenda/backend/tests

test-case10:
	pytest -q cases/10-onboarding-empleados/backend/tests

test-case13:
	pytest -q cases/13-bi-analista-datos/backend/tests

test-case19:
	pytest -q cases/19-devex-pr-review/backend/tests

test-case25:
	pytest -q cases/25-supervisor-workers/backend/tests

compile-case13:
	python -m compileall cases/13-bi-analista-datos/backend/src -q

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
