#!/usr/bin/env bash
set -euo pipefail

echo "== LangGraph Realworld Repo Installer =="
echo "Requisito: Docker Desktop instalado y corriendo."

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker no está disponible en PATH."
  exit 1
fi

echo "OK: docker encontrado."
echo ""
echo "Opciones:"
echo "  1) Levantar sitio estático (indexado) en http://localhost:8080"
echo "  2) Levantar Caso 09 (RR.HH) en http://localhost:8009"
echo "  3) Levantar ambos"
read -r -p "Elige (1/2/3): " opt

case "$opt" in
  1) docker compose up --build site ;;
  2) docker compose up --build case09 ;;
  3) docker compose up --build ;;
  *) echo "Opción inválida"; exit 1 ;;
esac
