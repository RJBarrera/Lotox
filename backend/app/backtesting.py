"""Backtesting cronológico de solo lectura. No confundir aciertos retrospectivos con predicción fiable."""
from collections import Counter
from random import Random

from .db import conexion_lectura
from .historial import MODALIDADES


def _sorteos_cronologicos(modalidad: str) -> list[tuple[int, ...]]:
    cfg = MODALIDADES[modalidad]
    columnas = ", ".join(cfg.columnas)
    # Identificadores tomados exclusivamente de un catálogo interno y estático.
    with conexion_lectura() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT {columnas} FROM {cfg.tabla} ORDER BY fecha ASC, concurso ASC")
            filas = cur.fetchall()
    sorteos = []
    for fila in filas:
        nums = tuple(sorted(int(fila[c]) for c in cfg.columnas))
        if len(set(nums)) != len(cfg.columnas) or not all(1 <= n <= cfg.maximo for n in nums):
            raise ValueError("El historial contiene números inválidos; revisa la modalidad y sus datos.")
        sorteos.append(nums)
    return sorteos


def _sorteo_ponderado(conteo: Counter, maximo: int, cuantos: int, rng: Random) -> tuple[int, ...]:
    opciones = list(range(1, maximo + 1))
    elegidos = []
    for _ in range(cuantos):
        pesos = [conteo[n] + 1 for n in opciones]
        elegido = rng.choices(opciones, weights=pesos, k=1)[0]
        elegidos.append(elegido)
        opciones.remove(elegido)
    return tuple(sorted(elegidos))


def _evaluar_filas(modalidad: str, sorteos: list[tuple[int, ...]], evaluaciones: int,
                   entrenamiento_minimo: int, ventana: int, semilla: int) -> dict:
    cfg = MODALIDADES[modalidad]
    if len(sorteos) < entrenamiento_minimo + 10:
        raise ValueError(f"Se necesitan al menos {entrenamiento_minimo + 10} sorteos para esta evaluación.")
    cantidad = min(evaluaciones, len(sorteos) - entrenamiento_minimo)
    inicio = len(sorteos) - cantidad
    estrategias = {name: Counter() for name in ("frecuencia", "clasica", "aleatoria")}
    totales = {name: 0 for name in estrategias}
    rng_ponderado = Random(semilla)
    rng_aleatorio = Random(semilla + 1)
    muestras = []
    for idx in range(inicio, len(sorteos)):
        # Solamente se consideran filas anteriores al sorteo evaluado (sin fuga temporal).
        previos = sorteos[max(0, idx - ventana):idx]
        conteo = Counter(n for numeros in previos for n in numeros)
        rango = list(range(1, cfg.maximo + 1))
        ranking = sorted(rango, key=lambda n: (-conteo[n], n))
        jugadas = {
            "frecuencia": _sorteo_ponderado(conteo, cfg.maximo, len(cfg.columnas), rng_ponderado),
            "clasica": tuple(sorted(ranking[:len(cfg.columnas)])),
            "aleatoria": tuple(sorted(rng_aleatorio.sample(rango, len(cfg.columnas)))),
        }
        real = set(sorteos[idx])
        por_estrategia = {}
        for nombre, jugada in jugadas.items():
            aciertos = len(set(jugada) & real)
            estrategias[nombre][aciertos] += 1
            totales[nombre] += aciertos
            por_estrategia[nombre] = aciertos
        if len(muestras) < 5:
            muestras.append({"indice_cronologico": idx + 1, "aciertos": por_estrategia})
    resumen = {}
    for nombre, distribucion in estrategias.items():
        resumen[nombre] = {
            "promedio_aciertos": round(totales[nombre] / cantidad, 4),
            "distribucion_aciertos": {str(k): distribucion.get(k, 0) for k in range(len(cfg.columnas) + 1)},
            "coincidencias_3_o_mas": sum(v for k, v in distribucion.items() if k >= 3),
        }
    return {
        "modalidad": modalidad, "sorteos_historicos": len(sorteos),
        "sorteos_entrenamiento_inicial": inicio, "sorteos_evaluados": cantidad,
        "ventana_entrenamiento": ventana, "semilla": semilla,
        "estrategias": resumen, "muestra": muestras,
        "metodologia": "Evaluación cronológica: cada jugada se calcula con sorteos anteriores exclusivamente; una jugada por estrategia y sorteo.",
        "advertencia": "Resultados retrospectivos descriptivos; no demuestran ventaja predictiva ni mayor probabilidad de ganar.",
    }


def evaluar_estrategias(modalidad: str, evaluaciones: int = 100, entrenamiento_minimo: int = 100,
                        ventana: int = 500, semilla: int = 42) -> dict:
    if modalidad not in MODALIDADES:
        raise ValueError("Modalidad no soportada.")
    if not (10 <= evaluaciones <= 500 and 30 <= entrenamiento_minimo <= 2000 and 30 <= ventana <= 5000):
        raise ValueError("Parámetros fuera de rango.")
    return _evaluar_filas(modalidad, _sorteos_cronologicos(modalidad), evaluaciones, entrenamiento_minimo, ventana, semilla)
