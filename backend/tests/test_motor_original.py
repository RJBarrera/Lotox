"""Pruebas aisladas de la adaptación del método original y repeticiones.

No abren conexiones a PostgreSQL, no escriben datos.
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import historial
from app import main


@pytest.mark.parametrize("modalidad", ["chispazo", "melate", "revancha", "revanchita"])
def test_metodo_clasico_es_determinista_y_usa_num_principales(monkeypatch, modalidad):
    cfg = historial.MODALIDADES[modalidad]
    # Ranking descendente de apariciones, independiente de la BD.
    ranking = [
        {"numero": n, "apariciones": cfg.maximo - n + 1}
        for n in range(1, cfg.maximo + 1)
    ]
    monkeypatch.setattr(historial, "frecuencias", lambda _modalidad, _ventana: {
        "ranking": ranking, "sorteos_analizados": 100,
    })
    r1 = historial.generar_combinaciones(modalidad, 5, 100, "clasica")
    r2 = historial.generar_combinaciones(modalidad, 5, 100, "clasica")
    assert r1 == r2
    assert r1["combinaciones"][0] == list(range(1, len(cfg.columnas) + 1))
    assert r1["combinaciones"][1] == list(range(2, len(cfg.columnas) + 2))
    assert len({tuple(x) for x in r1["combinaciones"]}) == 5
    for numeros in r1["combinaciones"]:
        assert len(numeros) == len(cfg.columnas)
        assert len(set(numeros)) == len(numeros)
        assert all(1 <= n <= cfg.maximo for n in numeros)


@pytest.mark.parametrize("modalidad", ["chispazo", "revanchita"])
def test_repeticiones_consulta_estatica_y_solo_lectura(monkeypatch, modalidad):
    cfg = historial.MODALIDADES[modalidad]
    sql = []
    fila = {c: n for n, c in enumerate(cfg.columnas, 1)}
    fila.update(repeticiones=2, ultima_fecha=date(2024, 4, 21))

    class FakeCursor:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def execute(self, query, params):
            sql.append((query, params))
        def fetchall(self):
            return [fila]

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

    from contextlib import contextmanager

    @contextmanager
    def fake_conexion():
        yield FakeConnection()

    monkeypatch.setattr(historial, "conexion_lectura", fake_conexion)
    respuesta = historial.combinaciones_repetidas(modalidad, 5)
    assert respuesta["modalidad"] == modalidad
    assert respuesta["data"][0]["numeros"] == list(range(1, len(cfg.columnas) + 1))
    assert respuesta["data"][0]["repeticiones"] == 2
    query, params = sql[0]
    assert query.startswith("SELECT ")
    assert f"FROM {cfg.tabla}" in query
    assert "HAVING COUNT(*) > 1" in query
    assert params == (5,)
    for column in cfg.columnas:
        assert column in query
    assert "r7" not in query


def test_rutas_nuevas_y_validaciones(monkeypatch):
    monkeypatch.setattr(main, "combinaciones_repetidas", lambda mod, limit: {
        "modalidad": mod, "data": [], "limite_prueba": limit,
    })
    monkeypatch.setattr(main, "generar_combinaciones", lambda mod, cantidad, ventana, estrategia: {
        "modalidad": mod, "estrategia": estrategia, "combinaciones": [],
    })
    client = TestClient(main.app)
    ok = client.get("/api/v1/modalidades/melate/combinaciones-repetidas?limite=5")
    assert ok.status_code == 200
    assert ok.json()["limite_prueba"] == 5
    assert client.get("/api/v1/modalidades/melate/combinaciones-repetidas?limite=11").status_code == 422
    assert client.get("/api/v1/modalidades/invalida/combinaciones-repetidas").status_code == 404
    clasica = client.get("/api/v1/modalidades/chispazo/predicciones?estrategia=clasica")
    assert clasica.status_code == 200
    assert clasica.json()["estrategia"] == "clasica"
    assert client.get("/api/v1/modalidades/chispazo/predicciones?estrategia=otro").status_code == 422
