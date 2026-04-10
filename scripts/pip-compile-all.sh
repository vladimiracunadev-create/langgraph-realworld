#!/usr/bin/env bash
# scripts/pip-compile-all.sh
# Generates deterministic lock files (requirements.txt) from requirements.in
# for all operational cases.
#
# Usage:
#   bash scripts/pip-compile-all.sh          # compile all
#   bash scripts/pip-compile-all.sh --check  # check for drift without regenerating
#
# Requires: pip-tools (pip install pip-tools)

set -euo pipefail

CHECK_MODE=false
if [[ "${1:-}" == "--check" ]]; then
  CHECK_MODE=true
fi

CASES=(
  "cases/01-soporte-cliente-omnicanal/backend"
  "cases/02-mesa-ayuda-ti-runbooks/backend"
  "cases/03-incident-response-sre/backend"
  "cases/09-rrhh-screening-agenda/backend"
  "cases/10-onboarding-empleados/backend"
  "cases/13-bi-analista-datos/backend"
  "cases/19-devex-pr-review/backend"
  "cases/25-supervisor-workers/backend"
)

if command -v pip-compile &> /dev/null; then
  PIP_COMPILE="pip-compile"
elif python -m piptools compile --version &> /dev/null 2>&1; then
  PIP_COMPILE="python -m piptools compile"
else
  echo "pip-compile not found. Install with: pip install pip-tools"
  exit 1
fi

STATUS=0

for case_dir in "${CASES[@]}"; do
  req_in="$case_dir/requirements.in"
  req_out="$case_dir/requirements.txt"

  if [[ ! -f "$req_in" ]]; then
    echo "SKIP  $req_in (not found)"
    continue
  fi

  if [[ "$CHECK_MODE" == true ]]; then
    echo "CHECK $req_in ..."
    if $PIP_COMPILE "$req_in" --output-file "$req_out" --check --quiet 2>&1; then
      echo "  OK  $req_out is up to date"
    else
      echo "  DRIFT detected in $req_out — run: bash scripts/pip-compile-all.sh"
      STATUS=1
    fi
  else
    echo "COMPILE $req_in -> $req_out ..."
    $PIP_COMPILE "$req_in" \
      --output-file "$req_out" \
      --strip-extras \
      --quiet
    echo "  DONE $req_out"
  fi
done

if [[ "$STATUS" -ne 0 ]]; then
  echo ""
  echo "ERROR: Some requirements.txt files are out of sync with their requirements.in."
  echo "Run: bash scripts/pip-compile-all.sh"
  exit 1
fi

echo ""
echo "All requirements.txt files are up to date."
