"""Configuración global de tests.

Aísla la base de datos de pruebas y elimina el contagio entre módulos de
tests (residuos de cursos/usuarios de un módulo rompiendo aserciones de
otro, y fixtures que borraban el archivo SQLite a mitad de sesión).

Orden exacto (verificado con réplicas):
1. conftest se importa ANTES que cualquier módulo de test: fija DATABASE_URL
   a un archivo SQLite temporal único por ejecución e importa
   app.database.session, de modo que el engine singleton (y las referencias
   tempranas en migrations.py y main.py) queden ligados SIEMPRE a la DB
   temporal. Los os.environ["DATABASE_URL"] de los módulos quedan sin efecto.
2. Los módulos de test fijan otras env vars (DEV_AUTH_ENABLED, claves de
   proveedor, etc.) en su import, DESPUÉS de que la Settings singleton fue
   creada. Para que esos valores no se congelen, la fixture autouse
   `_fresh_db_module` reconstruye Settings con el entorno actual y copia los
   campos sobre la MISMA instancia (mutations in-place, sin romper los
   `from app.core.config import settings` ya hechos), forzando luego
   DATABASE_URL de vuelta a la DB temporal.
3. Cada módulo arranca con esquema limpio: drop_all + create_all. El seed
   oficial vuelve a correr via el lifespan del TestClient de cada módulo.
4. Al terminar la sesión pytest se elimina el directorio temporal.

La vida de los datos DENTRO de un módulo no cambia (fixtures module-scope
comparten estado dentro del archivo, como siempre).
"""
import os
import shutil
import tempfile

_TMP_DIR = tempfile.mkdtemp(prefix="insoft-tests-")
_TEST_DB = os.path.join(_TMP_DIR, "test.db")
_TEST_DB_URL = f"sqlite:///{_TEST_DB}"
os.environ["DATABASE_URL"] = _TEST_DB_URL

os.environ.setdefault("OPENROUTER_GLOBAL_LIMIT_PER_MIN", "18")

import pytest  # noqa: E402

# Import temprano: crea la Settings singleton y el engine ligados a la DB
# temporal ANTES de que cualquier módulo de test pueda cambiar el entorno.
import app.database.session  # noqa: F401,E402
import app.models  # noqa: F401,E402 (registra modelos en la metadata)

from app.core import config as _config  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import engine as _engine  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _fresh_db_module():
    """DB temporal + Settings al día + esquema limpio por módulo de tests."""
    # Reconstruye Settings con el entorno del módulo (DEV_AUTH_ENABLED, etc.)
    # y cópiala in-place sobre la instancia existente para que todos los
    # `from app.core.config import settings` vean los valores nuevos.
    fresh = _config.Settings()
    _config.settings.__dict__.update(fresh.__dict__)
    # La ubicación de la DB es asunto de conftest: vuelve al archivo temporal.
    _config.settings.__dict__["DATABASE_URL"] = _TEST_DB_URL

    # Resetea contadores de rate limit: la DB nueva re-numera usuarios desde 1
    # y el limiter (en memoria) persistiría counts de módulos anteriores.
    from app.api.routes.ai import limiter

    try:
        limiter.reset()
    except Exception:
        storage = getattr(getattr(limiter, "_limiter", limiter), "_storage", None)
        if storage is not None:
            storage.reset()

    _engine.dispose()
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    yield
    _engine.dispose()
    Base.metadata.drop_all(bind=_engine)


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TMP_DIR, ignore_errors=True)
