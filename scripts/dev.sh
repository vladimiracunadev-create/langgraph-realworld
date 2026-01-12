#!/usr/bin/env bash
set -euo pipefail

TASK="${1:-lint}"

case "$TASK" in
  lint)   ruff check cases/09-rrhh-screening-agenda/backend/src ;;
  format) ruff format cases/09-rrhh-screening-agenda/backend/src ;;
  test)   pytest -q cases/09-rrhh-screening-agenda/backend/tests ;;
  up)     docker compose up --build ;;
  down)   docker compose down ;;
  *)
    echo "Unknown task: $TASK"
    echo "Usage: ./scripts/dev.sh [lint|format|test|up|down]"
    exit 1
    ;;
esac
