## Descripción

<!-- ¿Qué cambia este PR y por qué? 1–3 oraciones. -->

---

## Tipo de cambio

- [ ] Nuevo caso (scaffold → operativo / industrial)
- [ ] Mejora o corrección de caso existente
- [ ] Seguridad / hardening
- [ ] Documentación
- [ ] CI/CD / Infraestructura
- [ ] Otro: ___

## Casos afectados

<!-- Lista los casos modificados, ej: 01, 09 -->

---

## Checklist técnico

### Docker y contenedores

- [ ] `docker build` exitoso para todos los casos modificados
- [ ] Imagen base pineada a versión exacta (no `latest`, no tags flotantes)
- [ ] Proceso corre como usuario non-root
- [ ] Healthcheck usa binario disponible en la imagen

### Código y tests

- [ ] `ruff check` sin errores
- [ ] Tests existentes siguen pasando (`pytest -q`)
- [ ] Nuevos tests agregados si aplica

### Seguridad

- [ ] Sin secretos en el código (`.env` en `.gitignore`, solo `.env.example` commiteado)
- [ ] Puertos en `docker-compose.yml` con `127.0.0.1:PORT:PORT`
- [ ] Sin `shell=True` en subprocess

### Documentación

- [ ] README del caso actualizado (refleja el estado real)
- [ ] `CHANGELOG.md` actualizado si el cambio es significativo
- [ ] Links en el README apuntan a rutas válidas

### CI

- [ ] Pipeline CI pasa sin falsos positivos
- [ ] Pipeline de Security Scan pasa

---

## Notas adicionales

<!-- Contexto, limitaciones conocidas, decisiones de diseño o dependencias externas -->
