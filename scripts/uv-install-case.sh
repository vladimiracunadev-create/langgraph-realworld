#!/usr/bin/env bash
# scripts/uv-install-case.sh
#
# Instala las dependencias de un caso usando `$UV pip sync` (mucho más rápido que pip).
# Crea un venv aislado en cases/<caso>/backend/.venv si no existe.
#
# Uso:
#   bash scripts/uv-install-case.sh 06
#   bash scripts/uv-install-case.sh 14
#
# Requiere: uv (pip install uv  o  curl -LsSf https://astral.sh/uv/install.sh | sh)

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso: bash scripts/uv-install-case.sh <case_id>"
  echo "Ej:  bash scripts/uv-install-case.sh 06"
  exit 1
fi

CASE_ID="$1"

if command -v uv &> /dev/null; then
  UV="uv"
elif python -m uv --version &> /dev/null; then
  UV="python -m uv"
else
  echo "ERROR: 'uv' no está instalado. Ejecuta: pip install uv"
  exit 1
fi

CASE_DIR=$(find cases -maxdepth 1 -type d -name "${CASE_ID}-*" | head -1)
if [[ -z "$CASE_DIR" ]]; then
  echo "ERROR: caso ${CASE_ID} no encontrado en cases/"
  exit 1
fi

BACKEND="$CASE_DIR/backend"
if [[ ! -f "$BACKEND/requirements.txt" ]]; then
  echo "ERROR: $BACKEND/requirements.txt no existe (¿caso scaffold sin backend?)"
  exit 1
fi

VENV="$BACKEND/.venv"
if [[ ! -d "$VENV" ]]; then
  echo "Creando venv en $VENV con uv ..."
  $UV venv "$VENV" --python 3.11
fi

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    VENV_PY="$VENV/Scripts/python.exe"
    ;;
  *)
    VENV_PY="$VENV/bin/python"
    ;;
esac

echo "Instalando dependencias en $VENV ..."
$UV pip sync --python "$VENV_PY" "$BACKEND/requirements.txt"

echo ""
echo "Listo. Para activar:"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    echo "  source $VENV/Scripts/activate"
    ;;
  *)
    echo "  source $VENV/bin/activate"
    ;;
esac
echo "Para ejecutar el caso (ejemplo):"
echo "  cd $BACKEND && uvicorn src.api:app --port 80${CASE_ID}"
