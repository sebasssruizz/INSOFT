"""Controles de seguridad de bootstrap_remote: dry-run por defecto y confirmación de host.

No escribe en ninguna base: los pasos se sustituyen por funciones que fallan si se llaman.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DEV_AUTH_ENABLED", "true")

import pytest

from app.scripts import bootstrap_remote as br


@pytest.fixture()
def pasos_prohibidos(monkeypatch):
    def _no_debe_ejecutarse(*_a, **_k):
        raise AssertionError("un paso de escritura se ejecutó sin --apply")

    for nombre in ("step_schema", "step_content", "step_index"):
        monkeypatch.setattr(br, nombre, _no_debe_ejecutarse)


def _run(monkeypatch, *args):
    monkeypatch.setattr("sys.argv", ["bootstrap_remote", *args])
    return br.main()


def test_host_se_enmascara_sin_mostrar_credenciales():
    url = "postgresql+psycopg2://usuario:clave-secreta@ep-ejemplo-123.us-east-2.aws.neon.tech/db?sslmode=require"
    enmascarado = br.mask_host(url)
    assert "clave-secreta" not in enmascarado and "usuario" not in enmascarado
    assert "ep-ejemplo" not in enmascarado
    assert enmascarado.startswith("ep") and enmascarado.endswith("ch")


def test_host_corto_se_oculta_por_completo():
    assert br.mask_host("postgresql://u:p@db/x") == "*(2)*"


def test_dry_run_por_defecto_no_escribe(monkeypatch, pasos_prohibidos):
    assert _run(monkeypatch) == 0


def test_apply_sin_confirm_host_se_niega(monkeypatch, pasos_prohibidos):
    assert _run(monkeypatch, "--apply") == 2


def test_apply_con_host_equivocado_se_niega(monkeypatch, pasos_prohibidos):
    assert _run(monkeypatch, "--apply", "--confirm-host", "otra-base.example.com") == 2


def test_apply_con_la_mascara_no_vale_como_confirmacion(monkeypatch, pasos_prohibidos):
    mascara = br.mask_host(br.settings.DATABASE_URL)
    assert _run(monkeypatch, "--apply", "--confirm-host", mascara) == 2
