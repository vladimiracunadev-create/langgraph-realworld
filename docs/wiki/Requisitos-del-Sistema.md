# Requisitos del Sistema 📋

Antes de comenzar, asegúrese de que su máquina cumpla con los siguientes requisitos mínimos para garantizar una ejecución fluida de los agentes.

---

## 💻 Hardware Mínimo (Local)

- **CPU**: 4 núcleos (Intel i5/Ryzen 5 o superior).
- **RAM**: 8 GB (16 GB recomendado para correr múltiples casos en Docker).
- **Almacenamiento**: 5 GB+ (para logs históricos, bases de datos SQLite y volúmenes Docker).

### Escala / Extreme (Cargas de Producción)
- **CPU**: 8 Cores+ (Instancias tipo c6g.2xlarge en AWS).
- **RAM**: 32 GB.
- **Red**: Acceso estable con latencia < 150ms.

---

## 📡 Requisitos de Red

- **Ancho de Banda**: Mínimo 2 Mbps.
- **Puertos**: Rango `8000-8025` libre.

Consulte la lista detallada de dependencias en [REQUIREMENTS.md](../REQUIREMENTS.md).
