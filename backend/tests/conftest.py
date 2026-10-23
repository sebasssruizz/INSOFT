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
4. Insensibilidad al ORDEN de ejecución (F7): cada módulo de test declara y
   aplica sus overrides de entorno durante el import. Un import hook registra
   el os.environ resultante al FINAL del import de cada módulo
   (`_ENV_PER_MODULE`); el arranque de cada módulo de tests restaura ese
   entorno exacto y reconstruye Settings. El orden de COLECCIÓN (que determina
   los snapshots) es siempre alfabético y no se altera al aleatorizar el orden
   de EJECUCIÓN (pytest-randomly), por lo que cualquier permutación de
   ejecución produce el mismo entorno por módulo: la suite pasa igual con
   seeds aleatorias.
5. Al terminar la sesión pytest se elimina el directorio temporal.

La vida de los datos DENTRO de un módulo no cambia (fixtures module-scope
comparten estado dentro del archivo, como siempre).
"""
import importlib.machinery
import os
import shutil
import sys
import tempfile

_TMP_DIR = tempfile.mkdtemp(prefix="insoft-tests-")
_TEST_DB = os.path.join(_TMP_DIR, "test.db")
_TEST_DB_URL = f"sqlite:///{_TEST_DB}"
os.environ["DATABASE_URL"] = _TEST_DB_URL

# Secret de tests: el guard de producción exige SECRET_KEY real cuando
# DEV_AUTH_ENABLED=false, y la Settings singleton se crea antes de que los
# módulos fijen sus propias variables.
os.environ.setdefault("SECRET_KEY", "test-secret")

os.environ.setdefault("OPENROUTER_GLOBAL_LIMIT_PER_MIN", "18")

import pytest  # noqa: E402

# Import temprano: crea la Settings singleton y el engine ligados a la DB
# temporal ANTES de que cualquier módulo de test pueda cambiar el entorno.
import app.database.session  # noqa: F401,E402
import app.models  # noqa: F401,E402 (registra modelos en la metadata)

from app.core import config as _config  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import engine as _engine  # noqa: E402

# Snapshot del entorno al FINAL del import de cada módulo de test.
# Los módulos fijan sus overrides (DEV_AUTH_ENABLED, claves de proveedor...)
# en su import; registrarlas ahí (y no al arranque del conftest) es lo que
# permite a cada módulo arrancar con SU entorno sin que las mutaciones de
# runtime de módulos anteriores lo contaminen (orden-independiente).
_ENV_PER_MODULE: dict[str, dict[str, str]] = {}


class _EnvSnapshotFinder:
    """Meta path finder que envuelve el import de módulos `test_*`.

    Delega la búsqueda real en PathFinder y, tras ejecutar el módulo, guarda
    el os.environ resultante. La ejecución de tests nunca ocurre durante la
    colección, así que estos snapshots son estables ante aleatorización.
    """

    def find_spec(self, fullname, path=None, target=None):
        if not (fullname == "conftest" or fullname.startswith("test_") or fullname.startswith("tests.test_")):
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None or spec.loader is None or not hasattr(spec.loader, "exec_module"):
            return spec
        _orig_exec = spec.loader.exec_module

        def _exec_module_with_snapshot(module):
            _orig_exec(module)
            _ENV_PER_MODULE.setdefault(module.__name__, dict(os.environ))

        spec.loader.exec_module = _exec_module_with_snapshot  # type: ignore[method-assign]
        return spec


sys.meta_path.insert(0, _EnvSnapshotFinder())


@pytest.fixture(scope="module", autouse=True)
def _fresh_db_module(request):
    """DB temporal + entorno restaurado + Settings al día + esquema limpio."""
    # 1) entorno del módulo: resto las mutaciones de runtime de módulos
    #    anteriores y aplico el snapshot capturado al final del import de
    #    ESTE módulo (sus overrides incluidas). Si no hay snapshot (raro:
    #    módulo reimportado sin pasar por el hook) no toco nada.
    module_env = _ENV_PER_MODULE.get(request.module.__name__)
    if module_env is not None:
        os.environ.clear()
        os.environ.update(module_env)
    # 2) Reconstruye Settings con ese entorno (DEV_AUTH_ENABLED, etc.) y
    #    cópiala in-place sobre la instancia existente para que todos los
    #    `from app.core.config import settings` vean los valores nuevos.
    fresh = _config.Settings()
    _config.settings.__dict__.update(fresh.__dict__)
    # La ubicación de la DB es asunto de conftest: vuelve al archivo temporal.
    _config.settings.__dict__["DATABASE_URL"] = _TEST_DB_URL

    # Resetea contadores de rate limit: la DB nueva re-numera usuarios desde 1
    # y el limiter (en memoria) persistiría counts de módulos anteriores.
    from app.api.routes.ai import limiter
    from app.api.routes.practice import limiter as practice_limiter
    from app.api.routes.quiz import limiter as quiz_limiter

    _limiters = [limiter, practice_limiter, quiz_limiter]
    try:  # el limiter de auth existe en la rama de endurecimiento (no en staging hoy)
        from app.api.routes.auth import limiter as auth_limiter

        _limiters.append(auth_limiter)
    except ImportError:
        pass

    for _limiter in _limiters:
        try:
            _limiter.reset()
        except Exception:
            storage = getattr(getattr(_limiter, "_limiter", _limiter), "_storage", None)
            if storage is not None:
                storage.reset()

    # In-memory singletons de servicio: modelo de embeddings (lru_cache).
    from app.services import embeddings_service as _embeddings

    _embeddings._cached_embedding_model.cache_clear()

    _engine.dispose()
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    yield
    _engine.dispose()
    Base.metadata.drop_all(bind=_engine)


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TMP_DIR, ignore_errors=True)
