# Auditoría de seguridad y dependencias (4.3) — 2026-10-15

**Rama**: `chore/auditoria-seguridad` · Herramientas: `pip-audit 2.10.1`, `bandit 1.9.4`, `npm audit` (package-lock), escaneo de secretos por patrón.

## 1. Dependencias Python (`backend/requirements.txt`) — pip-audit/OSV

108 paquetes auditados. **Parcheados en esta rama** (subidas de versión menor, sin cambio de API):

| Paquete | Antes | Ahora | Resuelve |
|---|---|---|---|
| python-jose[cryptography] | 3.3.0 | **3.4.0** | PYSEC-2024-232/233 (des 2024); deja 1 CVE sin arreglo upstream |
| requests | 2.32.3 | **2.33.0** | PYSEC-2026-1872/2275 |
| python-multipart | 0.0.20 | **0.0.31** | PYSEC-2026-1852/3036-3040 (todos) |

Después del parcheo quedan **4 paquetes con hallazgos**, todos sin remedio
compatible con el árbol actual:

| Paquete | Vulns | Remedio | Estado |
|---|---|---|---|
| starlette 0.41.3 | 8 (PYSEC-2026-161/194x/228x/24x) | fixes ≥ 0.47.2…1.3.1 | Exige fastapi ≥1.0/: **pendiente de ventana de migración** (F9: plan de subida de framework). Mitigado: backend tras túnel, no pública directa |
| python-jose 3.4.0 | CVE-2026-85394 | sin arreglo publico hoy | Dispara solo con firma EC no estándar; en F8 (migrar a `pyjwt`/`google-genai`) desaparece |
| ecdsa 0.19.2 | PYSEC-2026-1325 | sin arreglo | Dep transitiva de python-jose: misma vía de salida |
| pyasn1 0.4.8 | 4 | 0.6.3/0.6.4 | Bloqueado por el pin de python-jose (pyasn1<0.5): misma vía de salida (F8) |

## 2. Dependencias del frontend — `npm audit --package-lock-only --omit=dev`

- **2 vulnerabilidades moderadas** (react-router + react-router-dom):
  "Open redirect via backslash en `<Link>/useNavigate` (CVE-2025-68470)" y
  "Constructor Injection via deserializeErrors() (SSR hydration)".
- Riesgo real en esta app: 1 (usamos `<Link>` interno con rutas fijas; no hay SSR en Vite, así que
  el vector de hydration no aplica). Pendiente de subir react-router en la siguiente
  ventana de actualización del frontend (no urgente).

## 3. Análisis estático del código — bandit

`bandit -r backend/app`: **0 HIGH, 3 MEDIUM, 3 LOW** (9551 LOC):

1. B608 en `database/migrations.py:128` — SQL f-string. Los identificadores
   vienen SIEMPRE del diccionario `NEW_COLUMNS` (constante en el código, no
   entrada del usuario) y el chequeo es doble. No arregla nada real.
2-3. B108 en `backend/app/scripts/run_qa_batch.py` (temp dir) — **script sin
   track todavía** (utilidad local de QA de pares; decidir si se versión o se
   borra antes de la próxima ronda).

## 4. Escaneo de secretos en git history

Patrones activos (OpenRouter `sk-or-v1-…`, Google `AIza…`, bloques `PRIVATE KEY`):
**ningún match**, ni en working tree ni en la muestra de los **60 últimos
commits** de `git rev-list --all` (limitación de muestra documentada; el PC
con .env real NO está en el repo). `backend/.env.example` solo placeholders.

## 5. Acciones esta rama

1. Las 3 subidas de versión de arriba (pip-audit revisado tras el parcheo).
2. `run_qa_batch.py` pendiente de decidir; NO versionado en este PR.
3. Informe + re-ejecución verificada en .venv real.

## Cómo reproducir

```bash
source backend/.venv/bin/activate
pip-audit -r backend/requirements.txt                # dependencias Python
bandit -r backend/app                                 # estático
npm --prefix frontend audit --package-lock-only --omit=dev  # frontend
```
