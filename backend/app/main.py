"""LotoX API: catálogo y análisis de PostgreSQL sin creación de tablas ni escritura."""

import logging
import os

import psycopg
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .backtesting import evaluar_estrategias
from .catalogo import COMPETENCIAS
from .db import DatabaseNotConfigured, conexion_lectura
from .historial import (
    configuracion, resumen, listar_sorteos, frecuencias, verificar_combinacion,
    generar_combinaciones, combinaciones_repetidas,
)

logger = logging.getLogger("lotox")

app = FastAPI(title="LotoX API", description="API de análisis estadístico de loterías. Solo lectura de PostgreSQL.", version="0.5.0")
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                   allow_methods=["GET"], allow_headers=["*"])


@app.exception_handler(DatabaseNotConfigured)
def no_configurado(_request, _exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=503, content={"detail": "Configura DATABASE_URL en backend/.env."})


@app.exception_handler(psycopg.Error)
def error_postgres(_request, exc):
    from fastapi.responses import JSONResponse
    logger.warning("Error de PostgreSQL: %s", type(exc).__name__)
    return JSONResponse(status_code=503, content={"detail": "No se pudo consultar PostgreSQL. Revisa conexión, permisos y estructura de tablas."})


def validar_modalidad(modalidad: str):
    if not configuracion(modalidad):
        raise HTTPException(status_code=404, detail="Modalidad no encontrada")


@app.get("/api/v1/health", tags=["Sistema"])
def health():
    return {"status": "ok", "service": "lotox-api", "version": "0.5.0"}


@app.get("/api/v1/db/health", tags=["Sistema"])
def db_health():
    with conexion_lectura() as conn:
        return {"status": "ok", "database": "postgresql"} if conn.execute("SELECT 1").fetchone() else {"status": "error"}


@app.get("/api/v1/competencias", tags=["Competencias"])
def listar_competencias():
    return {"data": COMPETENCIAS}


@app.get("/api/v1/modalidades/{modalidad}/resumen", tags=["Estadística"])
def obtener_resumen(modalidad: str):
    validar_modalidad(modalidad)
    return resumen(modalidad)


@app.get("/api/v1/modalidades/{modalidad}/historial", tags=["Estadística"])
def obtener_historial(modalidad: str, limite: int = Query(10, ge=1, le=100), pagina: int = Query(1, ge=1, le=100000)):
    validar_modalidad(modalidad)
    return {"modalidad": modalidad, "pagina": pagina, "limite": limite,
            "data": listar_sorteos(modalidad, limite, pagina)}


@app.get("/api/v1/modalidades/{modalidad}/frecuencias", tags=["Motor"])
def obtener_frecuencias(modalidad: str, ventana: int = Query(0, ge=0, le=20000)):
    validar_modalidad(modalidad)
    return frecuencias(modalidad, ventana)


@app.get("/api/v1/modalidades/{modalidad}/verificar", tags=["Motor"])
def verificar(modalidad: str, numeros: str = Query(..., description="Ejemplo: 1,4,7,12,20")):
    validar_modalidad(modalidad)
    try:
        partes = [int(x.strip()) for x in numeros.split(",")]
    except ValueError:
        raise HTTPException(status_code=422, detail="Los números deben ser enteros separados por comas.") from None
    try:
        return verificar_combinacion(modalidad, partes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/modalidades/{modalidad}/combinaciones-repetidas", tags=["Estadística"])
def obtener_combinaciones_repetidas(modalidad: str, limite: int = Query(5, ge=1, le=10)):
    validar_modalidad(modalidad)
    return combinaciones_repetidas(modalidad, limite)


@app.get("/api/v1/modalidades/{modalidad}/predicciones", tags=["Motor"])
def predicciones(modalidad: str, cantidad: int = Query(3, ge=1, le=5),
                 ventana: int = Query(500, ge=0, le=20000),
                 estrategia: str = Query("equilibrada", pattern="^(equilibrada|frecuencia|clasica)$")):
    validar_modalidad(modalidad)
    try:
        return generar_combinaciones(modalidad, cantidad, ventana, estrategia)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/modalidades/{modalidad}/backtesting", tags=["Motor"])
def backtesting(modalidad: str, evaluaciones: int = Query(100, ge=10, le=500),
                entrenamiento_minimo: int = Query(100, ge=30, le=2000),
                ventana: int = Query(500, ge=30, le=5000), semilla: int = Query(42, ge=0, le=2147483647)):
    validar_modalidad(modalidad)
    try:
        return evaluar_estrategias(modalidad, evaluaciones, entrenamiento_minimo, ventana, semilla)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
