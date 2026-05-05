#!/usr/bin/env bash
# scripts/uv-compile-all.sh
#
# Genera deterministas los requirements.txt desde requirements.in
# usando `$UV pip compile` (drop-in replacement de pip-compile, ~10x más rápido).
#
# Uso:
#   bash scripts/uv-compile-all.sh            # compila todo
#   bash scripts/uv-compile-all.sh --check    # solo verifica drift, no escribe
#
# Requiere: uv (https://docs.astral.sh/uv/  ·  pip install uv  o  curl -LsSf https://astral.sh/uv/install.sh | sh)

set -euo pipefail

CHECK_MODE=false
if [[ "${1:-}" == "--check" ]]; then
  CHECK_MODE=true
fi

CASES=(
  "cases/01-soporte-cliente-omnicanal/backend"
  "cases/02-mesa-ayuda-ti-runbooks/backend"
  "cases/03-incident-response-sre/backend"
  "cases/04-soc-triage-alertas/backend"
  "cases/05-analista-documentos/backend"
  "cases/06-compliance-auditorias/backend"
  "cases/08-ventas-b2b-crm/backend"
  "cases/09-rrhh-screening-agenda/backend"
  "cases/10-onboarding-empleados/backend"
  "cases/13-bi-analista-datos/backend"
  "cases/14-finanzas-conciliacion/backend"
  "cases/17-legal-intake/backend"
  "cases/19-devex-pr-review/backend"
  "cases/25-supervisor-workers/backend"
)

if command -v uv &> /dev/null; then
  UV="uv"
elif python -m uv --version &> /dev/null; then
  UV="python -m uv"
else
  echo "ERROR: 'uv' no está instalado."
  echo "  pip install uv     (o)"
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

STATUS=0

for case_dir in "${CASES[@]}"; do
  req_in="$case_dir/requirements.in"
  req_out="$case_dir/requirements.txt"

  if [[ ! -f "$req_in" ]]; then
    echo "SKIP   $case_dir (sin requirements.in)"
    continue
  fi

  if $CHECK_MODE; then
    tmp_out="$(mktemp)"
    if $UV pip compile "$req_in" --output-file "$tmp_out" --quiet 2>/dev/null; then
      if diff -q "$req_out" "$tmp_out" > /dev/null 2>&1; then
        echo "  OK    $req_out está actualizado"
      else
        echo "  DRIFT $req_out — ejecuta: bash scripts/uv-compile-all.sh"
        STATUS=1
      fi
    else
      echo "  ERROR no se pudo compilar $req_in"
      STATUS=1
    fi
    rm -f "$tmp_out"
  else
    echo "COMPILE $req_in -> $req_out ..."
    $UV pip compile "$req_in" \
      --output-file "$req_out" \
      --quiet
    echo "  DONE  $req_out"
  fi
done

if [[ "$STATUS" -ne 0 ]]; then
  echo ""
  echo "ERROR: Hay requirements.txt fuera de sincronía."
  echo "Ejecuta: bash scripts/uv-compile-all.sh"
  exit 1
fi

echo ""
echo "Todos los requirements.txt están actualizados."
