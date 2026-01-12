param(
  [ValidateSet("lint","format","test","up","down")]
  [string]$Task = "lint"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $MyInvocation.MyCommand.Path) | Out-Null
Set-Location ..

switch ($Task) {
  "lint"   { ruff check cases/09-rrhh-screening-agenda/backend/src }
  "format" { ruff format cases/09-rrhh-screening-agenda/backend/src }
  "test"   { pytest -q cases/09-rrhh-screening-agenda/backend/tests }
  "up"     { docker compose up --build }
  "down"   { docker compose down }
}
