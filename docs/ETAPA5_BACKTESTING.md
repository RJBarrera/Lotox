# LotoX v0.5 — Backtesting inicial (solo backend)

Este parche se aplica **sobre LotoX v0.4**, no sobre v0.3. Antes, haz respaldo de tus archivos.

## Archivos
- `backend/app/backtesting.py` — nuevo evaluador cronológico.
- `backend/app/main.py` — agrega el endpoint; se basa en `main.py` de v0.4.
- `backend/tests/test_backtesting.py` — pruebas aisladas.

No hay cambios a React, `.env`, esquema PostgreSQL ni datos históricos.

## Cómo probar
En la carpeta `backend` (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Endpoint: `GET /api/v1/modalidades/chispazo/backtesting?evaluaciones=100&entrenamiento_minimo=100&ventana=500&semilla=42`

También funciona con melate, revancha y revanchita.

Se compara una sola jugada por sorteo de las estrategias `frecuencia` (muestreo ponderado), `clasica` (los más frecuentes) y `aleatoria` (muestreo uniforme). Para cada sorteo se calcula exclusivamente con fechas anteriores. R7 de Melate queda fuera. La respuesta incluye distribución de aciertos, promedio, número de sorteos, semilla y parámetros. No prueba que una estrategia tenga ventaja real en un sorteo justo.

**Precaución:** si tu archivo `main.py` local cambió después de v0.4, compara diferencias antes de reemplazar. Este parche no fue probado con tu conexión de Railway; no incluye credenciales.
