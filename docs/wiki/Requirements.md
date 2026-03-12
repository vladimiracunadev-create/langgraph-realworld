# 📋 Requisitos del Sistema

> [!NOTE]
> **Versión**: 3.4.0 | **Estado**: Estable | **Audiencia**: Infraestructura, DevOps, Reclutadores

Especificaciones mínimas y recomendadas para ejecutar el portafolio de manera razonable.

---

## Hardware

### Mínimo

- CPU: 2 cores
- RAM: 4 GB
- Disco: 1 GB libre

### Recomendado

- CPU: 4 cores o más
- RAM: 8 GB a 16 GB
- Disco: 5 GB o más

---

## Software

- Windows 10/11 con WSL2, Linux moderno o macOS reciente
- Python 3.11+
- Docker Engine / Docker Desktop 24+
- Docker Compose 2+
- Git 2.34+

---

## Puertos Usados

- `8080`: portal principal
- `8009`: caso 09
- `8010`: caso 10
- `8013`: caso 13

---

## Navegadores

| Navegador | Estado |
| :--- | :--- |
| Chrome reciente | ✅ |
| Firefox reciente | ✅ |
| Safari reciente | ✅ |
| Internet Explorer | ❌ |

---

## Entornos Soportados

| Entorno | Portal | Casos industriales | Hub |
| :--- | :---: | :---: | :---: |
| Local con Python | ✅ | ✅ | ✅ |
| Docker | ✅ | ✅ | ✅ |
| Kubernetes | ⚠️ parcial | ⚠️ parcial | ❌ |