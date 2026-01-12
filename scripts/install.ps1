Write-Host "== LangGraph Realworld Repo Installer ==" -ForegroundColor Cyan
Write-Host "Requisito: Docker Desktop instalado y corriendo." -ForegroundColor Yellow

$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
  Write-Host "ERROR: docker no está disponible en PATH." -ForegroundColor Red
  exit 1
}

Write-Host "OK: docker encontrado." -ForegroundColor Green
Write-Host ""
Write-Host "Opciones:"
Write-Host "  1) Levantar sitio estático (indexado) en http://localhost:8080"
Write-Host "  2) Levantar Caso 09 (RR.HH) en http://localhost:8009"
Write-Host "  3) Levantar ambos"
$opt = Read-Host "Elige (1/2/3)"

if ($opt -eq "1") {
  docker compose up --build site
} elseif ($opt -eq "2") {
  docker compose up --build case09
} elseif ($opt -eq "3") {
  docker compose up --build
} else {
  Write-Host "Opción inválida" -ForegroundColor Red
  exit 1
}
