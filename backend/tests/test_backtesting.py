"""Pruebas unitarias sin conexiones externas ni alteraciones de PostgreSQL."""
import pytest
from fastapi.testclient import TestClient
from app import backtesting, main

@pytest.mark.parametrize("modalidad", ["chispazo", "melate", "revancha", "revanchita"])
def test_backtest_reproducible_y_sin_fuga_temporal(modalidad):
    cfg = backtesting.MODALIDADES[modalidad]
    k = len(cfg.columnas)
    datos = [tuple(sorted(((i + j * 3) % cfg.maximo) + 1 for j in range(k))) for i in range(165)]
    # Las 2 ejecuciones con la misma semilla son deterministas.
    primero = backtesting._evaluar_filas(modalidad, datos, 20, 100, 50, 17)
    segundo = backtesting._evaluar_filas(modalidad, datos, 20, 100, 50, 17)
    assert primero == segundo
    assert primero["sorteos_evaluados"] == 20
    for estrategia in primero["estrategias"].values():
        assert sum(estrategia["distribucion_aciertos"].values()) == 20

def test_solo_datos_anteriores_impactan_primer_pronostico(monkeypatch):
    # Si alteramos el último sorteo, NO debe cambiar la predicción para el sorteo anterior.
    cfg = backtesting.MODALIDADES["chispazo"]
    datos = [tuple(sorted(((i + j) % cfg.maximo) + 1 for j in range(5))) for i in range(150)]
    a = backtesting._evaluar_filas("chispazo", datos, 20, 100, 60, 7)
    datos[-1] = (1, 2, 3, 4, 5)
    b = backtesting._evaluar_filas("chispazo", datos, 20, 100, 60, 7)
    # La primera evaluación (índice 130) no puede cambiar por el resultado del índice 149.
    assert a["muestra"][0] == b["muestra"][0]

def test_validaciones_endpoint(monkeypatch):
    monkeypatch.setattr(main, "evaluar_estrategias", lambda *args: {"ok": True})
    client = TestClient(main.app)
    assert client.get("/api/v1/modalidades/chispazo/backtesting").status_code == 200
    assert client.get("/api/v1/modalidades/invalida/backtesting").status_code == 404
    assert client.get("/api/v1/modalidades/chispazo/backtesting?evaluaciones=900").status_code == 422
