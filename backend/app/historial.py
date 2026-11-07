"""Consultas parametrizadas a tablas existentes; sin operaciones de escritura."""

from dataclasses import dataclass
from random import Random
from secrets import SystemRandom

from .db import conexion_lectura


@dataclass(frozen=True)
class Configuracion:
    tabla: str
    columnas: tuple[str, ...]
    maximo: int
    adicional: str | None = None


MODALIDADES: dict[str, Configuracion] = {
    "chispazo": Configuracion("public.sorteos_chispazo", ("r1", "r2", "r3", "r4", "r5"), 28),
    "melate": Configuracion("public.sorteos_melate", ("r1", "r2", "r3", "r4", "r5", "r6"), 56, "r7"),
    "revancha": Configuracion("public.sorteos_revancha", ("r1", "r2", "r3", "r4", "r5", "r6"), 56),
    "revanchita": Configuracion("public.sorteos_revanchita", ("f1", "f2", "f3", "f4", "f5", "f6"), 56),
}


def configuracion(modalidad: str) -> Configuracion | None:
    return MODALIDADES.get(modalidad)


def resumen(modalidad: str) -> dict:
    cfg = MODALIDADES[modalidad]
    columnas = ", ".join(cfg.columnas + ((cfg.adicional,) if cfg.adicional else ()))
    with conexion_lectura() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS total, MIN(fecha) AS desde, MAX(fecha) AS hasta FROM {cfg.tabla}")
            meta = cur.fetchone()
            cur.execute(f"SELECT concurso, fecha, {columnas} FROM {cfg.tabla} ORDER BY fecha DESC, concurso DESC LIMIT 1")
            ultimo = cur.fetchone()
    if ultimo:
        ultimo = {
            "concurso": ultimo["concurso"],
            "fecha": ultimo["fecha"],
            "numeros": [ultimo[c] for c in cfg.columnas],
            "adicional": ultimo[cfg.adicional] if cfg.adicional else None,
        }
    return {"modalidad": modalidad, "registros": meta["total"], "desde": meta["desde"],
            "hasta": meta["hasta"], "ultimo": ultimo}


def listar_sorteos(modalidad: str, limite: int, pagina: int) -> list[dict]:
    cfg = MODALIDADES[modalidad]
    columnas = ", ".join(cfg.columnas + ((cfg.adicional,) if cfg.adicional else ()))
    with conexion_lectura() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT concurso, fecha, {columnas} FROM {cfg.tabla} "
                "ORDER BY fecha DESC, concurso DESC LIMIT %s OFFSET %s",
                (limite, (pagina - 1) * limite),
            )
            filas = cur.fetchall()
    return [{"concurso": fila["concurso"], "fecha": fila["fecha"],
             "numeros": [fila[c] for c in cfg.columnas],
             "adicional": fila[cfg.adicional] if cfg.adicional else None} for fila in filas]


def frecuencias(modalidad: str, ventana: int) -> dict:
    cfg = MODALIDADES[modalidad]
    columnas = ", ".join(cfg.columnas)
    valores = ", ".join(f"(h.{c})" for c in cfg.columnas)
    # 'ventana=0' significa todo el historial. Los identificadores son estáticos.
    limit_clause = "LIMIT %s" if ventana else ""
    params = (ventana,) if ventana else ()
    consulta = (
        f"WITH h AS (SELECT {columnas} FROM {cfg.tabla} "
        f"ORDER BY fecha DESC, concurso DESC {limit_clause}) "
        "SELECT v.numero AS numero, COUNT(*)::int AS apariciones "
        f"FROM h CROSS JOIN LATERAL (VALUES {valores}) AS v(numero) "
        "GROUP BY v.numero ORDER BY apariciones DESC, v.numero ASC"
    )
    with conexion_lectura() as conn:
        with conn.cursor() as cur:
            cur.execute(consulta, params)
            ranking = cur.fetchall()
    total_apariciones = sum(f["apariciones"] for f in ranking)
    sorteos_analizados = total_apariciones // len(cfg.columnas)
    # También devolvemos números nunca observados para generar con peso base.
    conteo = {f["numero"]: f["apariciones"] for f in ranking}
    ranking_completo = [
        {"numero": n, "apariciones": conteo.get(n, 0)}
        for n in range(1, cfg.maximo + 1)
    ]
    ranking_completo.sort(key=lambda r: (-r["apariciones"], r["numero"]))
    return {"modalidad": modalidad, "ventana": ventana,
            "sorteos_analizados": sorteos_analizados, "ranking": ranking_completo}


def verificar_combinacion(modalidad: str, numeros: list[int]) -> dict:
    cfg = MODALIDADES[modalidad]
    if len(numeros) != len(cfg.columnas) or len(set(numeros)) != len(numeros) or any(n < 1 or n > cfg.maximo for n in numeros):
        raise ValueError(f"Se necesitan {len(cfg.columnas)} números distintos entre 1 y {cfg.maximo}.")
    ordenados = sorted(numeros)
    condicion = " AND ".join(f"{col} = %s" for col in cfg.columnas)
    with conexion_lectura() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS veces FROM {cfg.tabla} WHERE {condicion}", tuple(ordenados))
            veces = cur.fetchone()["veces"]
            cur.execute(f"SELECT concurso, fecha FROM {cfg.tabla} WHERE {condicion} ORDER BY fecha DESC, concurso DESC LIMIT 5", tuple(ordenados))
            coincidencias = cur.fetchall()
    return {"modalidad": modalidad, "numeros": ordenados, "apariciones_historicas": veces,
            "ultimas_coincidencias": coincidencias}



def combinaciones_repetidas(modalidad: str, limite: int = 5) -> dict:
    """Devuelve solo combinaciones principales repetidas más de una vez.

    Los identificadores SQL salen exclusivamente del catálogo estático MODALIDADES.
    No mezcla R7, ni utiliza información de otra modalidad.
    """
    cfg = MODALIDADES[modalidad]
    columnas = ", ".join(cfg.columnas)
    consulta = (
        f"SELECT {columnas}, COUNT(*)::int AS repeticiones, MAX(fecha) AS ultima_fecha "
        f"FROM {cfg.tabla} GROUP BY {columnas} HAVING COUNT(*) > 1 "
        f"ORDER BY repeticiones DESC, ultima_fecha DESC, {columnas} LIMIT %s"
    )
    with conexion_lectura() as conn:
        with conn.cursor() as cur:
            cur.execute(consulta, (limite,))
            filas = cur.fetchall()
    return {
        "modalidad": modalidad,
        "data": [
            {
                "numeros": [fila[col] for col in cfg.columnas],
                "repeticiones": fila["repeticiones"],
                "ultima_fecha": fila["ultima_fecha"],
            }
            for fila in filas
        ],
    }


def _muestra_ponderada_sin_reemplazo(pesos: list[tuple[int, float]], cantidad: int, rng: Random) -> list[int]:
    disponibles = list(pesos)
    resultado: list[int] = []
    for _ in range(cantidad):
        peso_total = sum(peso for _, peso in disponibles)
        umbral = rng.random() * peso_total
        acumulado = 0.0
        elegido = len(disponibles) - 1
        for i, (_num, peso) in enumerate(disponibles):
            acumulado += peso
            if umbral < acumulado:
                elegido = i
                break
        resultado.append(disponibles.pop(elegido)[0])
    return sorted(resultado)


def generar_desde_ranking(cfg: Configuracion, ranking: list[dict], cantidad: int,
                         estrategia: str, rng: Random | None = None) -> list[list[int]]:
    """Motor compartido: no consulta datos ni conoce el sorteo que será evaluado."""
    if not 1 <= cantidad <= 5:
        raise ValueError("La cantidad debe estar entre 1 y 5.")
    # Método de los cuatro Python originales: ventanas consecutivas del ranking
    # de números más frecuentes. Es determinista para un mismo historial/ventana.
    if estrategia == "clasica":
        numeros = [fila["numero"] for fila in ranking]
        tamano = len(cfg.columnas)
        combinaciones = [sorted(numeros[i:i + tamano]) for i in range(cantidad)]
    else:
        conteos = {f["numero"]: f["apariciones"] for f in ranking}
        media = sum(conteos.values()) / cfg.maximo
        if estrategia == "frecuencia":
            pesos = [(numero, float(conteos[numero] + 1)) for numero in range(1, cfg.maximo + 1)]
        elif estrategia == "equilibrada":
            pesos = [(numero, 0.5 + 0.5 * ((conteos[numero] + 1) / (media + 1))) for numero in range(1, cfg.maximo + 1)]
        else:
            raise ValueError("Estrategia desconocida.")
        rng = rng if rng is not None else SystemRandom()
        combinaciones: list[list[int]] = []
        vistos: set[tuple[int, ...]] = set()
        for _ in range(250):
            combinacion = _muestra_ponderada_sin_reemplazo(pesos, len(cfg.columnas), rng)
            llave = tuple(combinacion)
            if llave not in vistos:
                combinaciones.append(combinacion)
                vistos.add(llave)
            if len(combinaciones) == cantidad:
                break
        if len(combinaciones) != cantidad:
            raise ValueError("No se pudieron generar suficientes combinaciones distintas.")
    return combinaciones


def generar_combinaciones(modalidad: str, cantidad: int, ventana: int, estrategia: str) -> dict:
    cfg = MODALIDADES[modalidad]
    datos = frecuencias(modalidad, ventana)
    if not datos["sorteos_analizados"]:
        raise ValueError("No hay sorteos históricos disponibles para generar combinaciones.")
    combinaciones = generar_desde_ranking(cfg, datos["ranking"], cantidad, estrategia)
    return {"modalidad": modalidad, "estrategia": estrategia, "ventana": ventana,
            "sorteos_analizados": datos["sorteos_analizados"], "combinaciones": combinaciones,
            "advertencia": "Son combinaciones heurísticas, no predicciones con ventaja matemática. En sorteos justos todas las combinaciones válidas son equiprobables."}
