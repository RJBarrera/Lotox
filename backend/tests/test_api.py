"""Pruebas mínimas de la primera etapa."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_salud():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_competencias():
    response = client.get("/api/v1/competencias")
    assert response.status_code == 200
    data = response.json()["data"]
    assert {x["id"] for x in data} == {"chispazo", "melate"}
    melate = next(x for x in data if x["id"] == "melate")
    assert {m["id"] for m in melate["modalidades"]} == {
        "melate", "revancha", "revanchita"
    }
