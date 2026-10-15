"""§13: peticiones ante BD suspendida/agotada nunca se cuelgan.

- Agotamiento del pool → sqlalchemy TimeoutError → 503 db_unavailable.
- Fallo de conexión (OperationalError) → 503 db_unavailable + Retry-After.
- El listener de statement_timeout NO se registra con sqlite (tests).

Sin red ni proveedores: usa sqlite y un engine QueuePool artificial.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402
from sqlalchemy.exc import TimeoutError as PoolTimeoutError  # noqa: E402
from sqlalchemy.pool import QueuePool  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _registrar_rutas_de_fallo(temporal_app: FastAPI) -> None:
    @temporal_app.get("/_prueba/pool-agotado")
    def pool_agotado():
        raise PoolTimeoutError()

    @temporal_app.get("/_prueba/bd-caida")
    def bd_caida():
        raise OperationalError("stmt", {}, Exception("connect_timeout"))


def _app_con_mismos_manejadores() -> FastAPI:
    """App mínima que reutiliza los manejadores registrados en app.main."""
    temporal = FastAPI(exception_handlers=dict(app.exception_handlers))
    _registrar_rutas_de_fallo(temporal)
    return temporal


def test_pool_agotado_responde_503_y_no_cuelga():
    c = TestClient(_app_con_mismos_manejadores(), raise_server_exceptions=False)
    r = c.get("/_prueba/pool-agotado")
    assert r.status_code == 503
    assert r.json()["error"] == "db_unavailable"
    assert r.headers.get("Retry-After") == "5"


def test_bd_caida_responde_503_y_no_cuelga():
    c = TestClient(_app_con_mismos_manejadores(), raise_server_exceptions=False)
    r = c.get("/_prueba/bd-caida")
    assert r.status_code == 503
    assert r.json()["error"] == "db_unavailable"
    assert r.headers.get("Retry-After") == "5"


def test_valores_por_defecto_timeouts():
    assert settings.DB_POOL_TIMEOUT == 10
    assert settings.DB_STATEMENT_TIMEOUT_S == 15
    assert settings.DB_CONNECT_TIMEOUT == 10


def test_agotamiento_real_del_pool_falla_rapido():
    """Cola de 1 conexión sin overflow y timeout=0: el segundo checkout lanza
    TimeoutError (equivalente a pool saturado: no espera indefinidamente)."""

    class _ConexiónFake:
        marca = 0

        def close(self):
            pass

    pool = QueuePool(creator=_ConexiónFake, pool_size=1, max_overflow=0, timeout=0)
    con1 = pool.connect()
    try:
        with pytest.raises(PoolTimeoutError):
            pool.connect()
    finally:
        con1.close()
        pool.dispose()
