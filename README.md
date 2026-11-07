# LotoX

Plataforma de análisis y generación de combinaciones de lotería. Frontend React + Vite, backend Python + FastAPI y consultas a PostgreSQL de Railway.

## Competencias

- Chispazo: 5 números entre 1 y 28.
- Melate: 6 números principales entre 1 y 56, con R7 adicional informativo.
- Revancha: 6 números entre 1 y 56.
- Revanchita: 6 números entre 1 y 56, con columnas `f1` a `f6`.

## Reglas de datos

La base de datos y las tablas son administradas exclusivamente por el usuario. El backend no crea tablas, migra esquemas ni importa CSV. Se conecta con transacciones de solo lectura. No subir nunca `.env` a GitHub ni compartir un ZIP que lo contenga.

## Ejecutar localmente (PowerShell)

Backend (desde `backend`):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Crear `backend/.env` localmente con `DATABASE_URL` y `CORS_ORIGINS` (no versionarlo). Para conexiones desde Windows a Railway se usa la URL pública o un túnel autorizado.

Frontend (desde `frontend`, otra terminal):

```powershell
npm install
npm run dev
```

Abrir `http://127.0.0.1:5173` y consultar el Swagger de FastAPI en `http://127.0.0.1:8000/docs`.

## Pruebas

```powershell
# Desde frontend
npm test
npm run build

# Desde backend, con dependencias de desarrollo instaladas
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q tests/test_api.py tests/test_motor.py tests/test_motor_original.py
```

Las pruebas contra PostgreSQL real están separadas y requieren habilitación expresa (`LOTOX_TEST_DATABASE=1`). Revisar `docs/VALIDACION_ETAPA3.md`.

## Motor v0.4

Estrategias disponibles: `equilibrada`, `frecuencia` y `clasica` (método de los Python originales). Se añadió el endpoint para combinaciones repetidas del historial. Documentación: [`docs/ETAPA4_MOTOR_ORIGINAL.md`](docs/ETAPA4_MOTOR_ORIGINAL.md).

**Nota:** son heurísticas y análisis descriptivos. No existe evidencia de ventaja matemática sobre una selección uniforme en sorteos justos.

## Backtesting del motor

Cada modalidad incluye una evaluación cronológica de las tres estrategias frente
a selecciones aleatorias uniformes, con semilla reproducible, distribución de
aciertos y detalle de propuestas por sorteo. Solo utiliza datos anteriores y no
escribe en PostgreSQL. Consulta la [metodología, API y estado de validación](docs/BACKTESTING.md).
