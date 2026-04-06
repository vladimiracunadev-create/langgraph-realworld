# Decisiones de diseño descartadas

> [!NOTE]
> Este documento registra enfoques que fueron evaluados y **descartados** durante el desarrollo del repositorio,
> con la razón por la que no se adoptaron. Sirve como memoria técnica para evitar reintroducir los mismos patrones.

---

## Seguridad y contenedores

### `shell=True` en Hub CLI

**Descartado**: ejecución de comandos de `case.yml` con `subprocess.run(shell=True)`.

**Por qué se descartó**: permite inyección de comandos si algún campo del YAML contiene metacaracteres.
Se reemplazó por una lista de ejecutables permitidos (`python`, `uvicorn`, `docker compose`) con validación explícita.

---

### Puertos expuestos en `0.0.0.0` en docker-compose

**Descartado**: mapeo de puertos sin vincular a interfaz específica (ej: `"8001:8001"`).

**Por qué se descartó**: permite conexiones desde cualquier máquina en la red local, no solo desde `localhost`.
Todos los puertos ahora usan `127.0.0.1:PORT:PORT`.

---

### Tags `latest` o sin versión en imágenes Docker

**Descartado**: `FROM nginx:alpine` y `FROM python:3.11-slim` sin parche fijo.

**Por qué se descartó**: los tags mutables hacen que las builds no sean reproducibles y pueden introducir
vulnerabilidades silenciosamente. Ahora se usan `nginx:1.27.3-alpine` y `python:3.11.10-slim`.

---

### Healthcheck con `curl` en imágenes Alpine

**Descartado**: `HEALTHCHECK CMD curl -f http://localhost:8080/`.

**Por qué se descartó**: `curl` no está instalado en `nginx:alpine`. El healthcheck fallaba silenciosamente.
Se reemplazó por `wget --spider` (disponible vía BusyBox en Alpine sin instalación adicional).

---

## CI/CD

### Trivy para escaneo de imágenes Docker

**Descartado**: acción `aquasecurity/trivy-action` para escaneo de vulnerabilidades.

**Por qué se descartó**: incidente de supply chain conocido que afectó el canal de distribución de Trivy.
Se adoptó `anchore/scan-action` (grype) pineado a SHA de commit como alternativa auditada.

---

### Dependencias sin auditoría automática

**Descartado**: `requirements.txt` sin revisión periódica de CVEs.

**Por qué se descartó**: vulnerabilidades en dependencias transitivas pueden pasar desapercibidas.
Se implementaron `pip-audit` en CI y Dependabot para notificación automática.

---

> [!TIP]
> Para el estado de seguridad actual y los controles vigentes, ver [SECURITY.md](SECURITY.md).
