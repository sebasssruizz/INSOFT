"""Los fallos internos no deben quedar ocultos como errores de red por CORS."""
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app


def test_internal_error_has_json_cors_and_request_id_without_exposing_details(monkeypatch):
    monkeypatch.setattr(settings, "BACKEND_CORS_ORIGINS", "http://localhost:5173")
    monkeypatch.setattr(settings, "BACKEND_CORS_ORIGIN_REGEX", "")
    app = create_app()

    @app.get("/test-internal-error")
    def broken():
        raise RuntimeError("detalle-interno-no-publicar")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test-internal-error", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["x-request-id"]
    assert response.json()["detail"].startswith("[error-interno]")
    assert "detalle-interno-no-publicar" not in response.text

    denied = client.get("/test-internal-error", headers={"Origin": "https://no-autorizado.invalid"})
    assert "access-control-allow-origin" not in denied.headers
