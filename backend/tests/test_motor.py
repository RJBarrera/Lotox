"""Pruebas puras del motor. No requieren DATABASE_URL ni escriben en PostgreSQL."""

import pytest
from app import historial


def test_modalidades_y_columnas():
    assert set(historial.MODALIDADES) == {"chispazo", "melate", "revancha", "revanchita"}
    assert historial.MODALIDADES["revanchita"].columnas == tuple(f"f{i}" for i in range(1, 7))
    assert historial.MODALIDADES["melate"].adicional == "r7"


def test_muestreo_sin_reemplazo():
    rng = historial.SystemRandom()
    result = historial._muestra_ponderada_sin_reemplazo([(i, 1.0) for i in range(1, 29)], 5, rng)
    assert len(result) == 5
    assert sorted(result) == result
    assert len(set(result)) == 5
    assert all(1 <= n <= 28 for n in result)


@pytest.mark.parametrize("modo,cantidad,maximo", [
    ("chispazo", 5, 28), ("melate", 6, 56),
    ("revancha", 6, 56), ("revanchita", 6, 56),
])
def test_generar_combinaciones_sin_bd(monkeypatch, modo, cantidad, maximo):
    monkeypatch.setattr(historial, "frecuencias", lambda _modo, ventana: {
        "sorteos_analizados": 500,
        "ranking": [{"numero": n, "apariciones": 100} for n in range(1, maximo + 1)],
    })
    for estrategia in ("equilibrada", "frecuencia"):
        resultado = historial.generar_combinaciones(modo, 3, 500, estrategia)
        assert len(resultado["combinaciones"]) == 3
        assert len({tuple(x) for x in resultado["combinaciones"]}) == 3
        for nums in resultado["combinaciones"]:
            assert len(nums) == cantidad
            assert nums == sorted(nums)
            assert len(set(nums)) == cantidad
            assert 1 <= nums[0] and nums[-1] <= maximo


def test_verificar_no_acepta_rangos_invalidos():
    with pytest.raises(ValueError):
        historial.verificar_combinacion("chispazo", [1, 2, 3, 4, 29])
    with pytest.raises(ValueError):
        historial.verificar_combinacion("melate", [1, 2, 3, 4, 5, 5])
